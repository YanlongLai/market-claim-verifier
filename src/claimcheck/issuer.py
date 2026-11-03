"""Exact SEC issuer binding. Ticker substrings and fuzzy names are never identity."""
from __future__ import annotations

import re
from typing import Any

# Reviewed trade names, keyed by SEC CIK rather than a model-proposed ticker.
# The SEC map must still contain the CIK/ticker pair on every use.
ALIASES = {
    "0001326801": ("Meta", "Facebook"),
    "0001652044": ("Alphabet", "Google", "Google Cloud"),
    "0001018724": ("Amazon", "AWS", "Amazon Web Services"),
    "0000320193": ("Apple", "蘋果", "苹果"), "0000789019": ("Microsoft", "微軟", "微软"),
    "0001045810": ("Nvidia", "輝達", "英伟达"), "0000731766": ("UnitedHealth", "UnitedHealth Group"),
    "0001287750": ("Ares Capital",), "0000829224": ("Starbucks",),
    "0001306965": ("Shell",), "0001559720": ("Airbnb",),
    "0001075531": ("Booking", "Booking Holdings"),
    "0001648416": ("Alibaba",), "0000909832": ("Costco",),
    "0001730168": ("Broadcom",), "0001099590": ("Five Below",),
    "0001035267": ("Intuitive Surgical",), "0001058090": ("Chipotle",),
    "0001571996": ("Dell",), "0000773840": ("Honeywell",),
    "0000002488": ("AMD", "Advanced Micro Devices"),
    "0000050863": ("Intel",), "0001318605": ("Tesla",),
    "0001834584": ("Coupang",),
}


def normalized_name(text: str) -> str:
    text = re.sub(r"\b(?:incorporated|inc|corporation|corp|ltd|limited|plc|company|co|holdings)\b", " ", text, flags=re.I)
    return " ".join(re.findall(r"[a-z0-9\u3400-\u9fff]+", text.lower()))


def name_agrees(text: str, company: dict) -> bool:
    # Preserve word boundaries: Hon Precision cannot match HON or Honeywell.
    haystack = " " + normalized_name(text) + " "
    names = [normalized_name(str(company.get("entity", ""))), *(
        normalized_name(n) for n in ALIASES.get(str(company.get("cik")), ()))]
    return any((len(n) >= 3 and " " + n + " " in haystack) or
               (re.search(r"[\u3400-\u9fff]", n) and n in text) for n in names)


def outside_sec_scope(text: str, country: str | None = None) -> bool:
    return str(country or "").upper() in {"TW", "TWN", "TAIWAN"} or bool(
        re.search(r"\b(?:TWD|TWSE|TPEX|MOPS)\b|新[臺台]幣|台股|臺股", text, re.I))


def bind_issuer(edgar: Any, text: str, ticker: str, *, country: str | None = None,
                exchange: str | None = None) -> dict:
    company = edgar.resolve_ticker(ticker)
    if outside_sec_scope(text, country) or company.get("error") or not name_agrees(text, company):
        return {"error": "issuer not in SEC coverage", "reason": "exact SEC issuer name/CIK agreement required; ticker letters and fuzzy names are not identity",
                "requested_ticker": ticker}
    if exchange:
        doc, _ = edgar._load_document("company_tickers_exchange.json", "https://www.sec.gov/files/company_tickers_exchange.json")
        rows = [dict(zip(doc.get("fields", []), row)) for row in doc.get("data", [])]
        match = [r for r in rows if str(r.get("ticker", "")).upper() == ticker.upper()
                 and str(r.get("cik", "")).lstrip("0") == company["cik"].lstrip("0")]
        if not match or str(match[0].get("exchange", "")).casefold() != exchange.casefold():
            return {"error": "issuer not in SEC coverage", "reason": "SEC exchange/CIK mismatch"}
    if country and country.upper() not in {"TW", "TWN", "TAIWAN"}:
        doc, _ = edgar._load_document(f"submissions-CIK{company['cik']}.json",
                                     f"https://data.sec.gov/submissions/CIK{company['cik']}.json")
        address = doc.get("addresses", {}).get("business", {})
        code = str(address.get("stateOrCountry", ""))
        description = str(address.get("stateOrCountryDescription", ""))
        us_states = set("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split())
        agrees = (country.upper() in {"US", "USA", "UNITED STATES"} and code in us_states) or country.casefold() == description.casefold()
        if not agrees:
            return {"error": "issuer not in SEC coverage", "reason": "SEC country/CIK mismatch or missing country evidence"}
    return {**company, "issuer_bound": True, "binding": "exact SEC name or reviewed CIK alias",
            "exchange": exchange, "country": country}


def identify_issuer(edgar: Any, text: str) -> dict:
    """Find a unique exact name in the SEC map; never infer from ticker letters."""
    doc, _ = edgar._ticker_document()
    matches = {}
    records = doc.get("data", []) if isinstance(doc.get("data"), list) else doc.values()
    for record in records:
        if not isinstance(record, dict) or not record.get("ticker") or not record.get("title") or record.get("cik_str") is None:
            continue
        company = {"ticker": record["ticker"], "cik": f"{int(record['cik_str']):010d}", "entity": record.get("title", "")}
        if name_agrees(text, company):
            matches[company["cik"]] = company
    if len(matches) != 1:
        return {"error": "issuer not in SEC coverage", "reason": "missing or ambiguous exact SEC issuer name"}
    return next(iter(matches.values()))


def quote_issuer_context(edgar: Any, quote: str, source: str) -> tuple[str, dict | None]:
    """A generic table/pronoun quote can inherit one exact named source issuer.

    A named unknown issuer (such as Hon Precision) cannot inherit another
    company from elsewhere in a multi-company post.
    """
    if not re.match(r"\s*(?:its\b|the company\b|release table\b|total\b|net\b|revenue\b|quarterly\b|diluted\b|EPS\b|sales\b)", quote, re.I):
        return quote, None
    try:
        company = identify_issuer(edgar, source)
        source_name = normalized_name(source)
        # A source can introduce the issuer after an explicit synthetic-narrator
        # disclosure. This prefix contains no entity or financial assertion.
        source_name = re.sub(r"^(?:example recording )?a synthetic narrator is reading ", "", source_name)
        names = [normalized_name(company.get("entity", "")), *(normalized_name(n) for n in ALIASES.get(company.get("cik"), ()))]
        if not company.get("error") and any(n and source_name.startswith(n + " ") for n in names):
            return source, {**company, "scope": "unique exact issuer named in original source; generic quote"}
    except (AttributeError, RuntimeError, OSError):
        pass
    return quote, None
