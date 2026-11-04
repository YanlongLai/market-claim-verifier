"""Deterministic, cited numeric edits over original text. No model or I/O.

Inputs are *program checks*, never a model verdict/summary or proposed rewrite.
Offsets count Python Unicode code points (including astral characters). Consumers
must use that convention, or render the original/replacement strings as text.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, ROUND_HALF_UP, localcontext
import re
from typing import Any
from urllib.parse import urlsplit

from .issuer import ALIASES, name_agrees
from .release import METRIC_PATTERNS, claim_periods

LABEL = {
    "en": "Corrected draft — only listed assertions checked",
    "zh": "修正版草稿——僅核對列出的主張",
}
REASONS = {
    "supported": ("The program supports this assertion; no edit needed.", "程式支持此主張，無須修改。"),
    "not_judged": ("This assertion was not judged (opinion or out of scope).", "此主張未評判（意見或超出範圍）。"),
    "insufficient_evidence": ("Insufficient evidence; this assertion was not corrected.", "證據不足，未修正此主張。"),
    "not_contradicted": ("No program contradiction was established.", "程式未確認此主張與證據矛盾。"),
    "non_numeric": ("This assertion has no supported numeric substitution.", "此主張無可支援的數值替換。"),
    "invalid_evidence": ("The program did not validate sufficient numeric evidence.", "程式未確認有充分的數值證據。"),
    "ambiguous_period": ("The checked period is ambiguous or does not match the original span.", "核對期間不明確，或與原文片段不符。"),
    "missing_citation": ("A referenced filing or component filing cannot be cited.", "無法引用所需的申報文件或計算組成文件。"),
    "ambiguous_evidence": ("The numeric value, unit and evidence do not bind uniquely.", "數值、單位與證據無法唯一對應。"),
    "unsupported_wording": ("Replacing the number alone would not correct this wording.", "僅替換數字無法修正此措辭。"),
    "span_not_found": ("No matching number with the stated unit was found in the original text.", "原文中找不到相符數字與單位。"),
    "ambiguous_span": ("More than one original span could match this assertion.", "原文中有多個可能對應此主張的片段。"),
    "ambiguous_context": ("The original span does not uniquely identify the checked issuer and metric.", "原文片段無法唯一對應核對的公司與財務指標。"),
    "overlapping_spans": ("Proposed edits overlap; the original text is retained.", "擬修改的片段重疊，保留原文。"),
}

_SCALES = {
    "trillion": 10**12, "trillions": 10**12, "tn": 10**12, "t": 10**12, "兆": 10**12,
    "billion": 10**9, "billions": 10**9, "bn": 10**9, "b": 10**9, "十億": 10**9,
    "million": 10**6, "millions": 10**6, "mn": 10**6, "m": 10**6, "百萬": 10**6,
    "thousand": 10**3, "thousands": 10**3, "k": 10**3, "千": 10**3,
    "億": 10**8, "萬": 10**4,
}
_AMOUNT = re.compile(
    r"(?<![\d.,])(?P<sign>[+−-]?)(?P<currency>(?:US\$|NT\$|HK\$|[CA]\$|USD|TWD|EUR|GBP|CAD|AUD|HKD|CNY|JPY|RMB|美元|美金|新[台臺]幣|港幣|港元|人民幣|歐元|英鎊|[$€£¥])[ \t]*)?"
    r"(?P<number>[+−-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)"
    r"(?:[ \t]*(?P<scale>trillions?|billions?|millions?|thousands?|percent|tn|bn|mn|[tbmk%％]|十億|百萬|億|萬|兆|千)(?![A-Za-z]))?"
    r"(?:[ \t]*(?P<suffix>美元|美金|新[台臺]幣|港幣|港元|人民幣|歐元|英鎊|元|股|shares\b|USD\b|TWD\b|EUR\b|GBP\b|CAD\b|AUD\b|HKD\b|CNY\b|JPY\b))?"
    r"(?!\d|[.,]\d|[A-Za-z])", re.I,
)
_QUALITATIVE = re.compile(r"\b(?:first(?:[ -]ever| time)|record|all[ -]time|highest|lowest)\b|首次|史上|創紀錄|創新高|歷史新高", re.I)
_DOWN = re.compile(r"\b(?:fell|fallen|falling|declin(?:e[sd]?|ing)|decreas(?:e[sd]?|ing)|drop(?:s|ped|ping)?|down)\b|下降|下滑|下跌|減少", re.I)
_UP = re.compile(r"\b(?:rose|rise[sn]?|rising|increas(?:e[sd]?|ing)|grew|grown|growing|up)\b|成長|增長|增加|上升", re.I)
_RANGE_OR_COMPOUND = re.compile(r"\bbetween\b|\bfrom\b.{0,60}\bto\b|介於|區間|\d[\d,.]*\s*(?:兆|億|萬|千)\s+\d", re.I)


def _direction(text: str) -> int:
    down, up = bool(_DOWN.search(text)), bool(_UP.search(text))
    return 2 if down and up else -1 if down else 1 if up else 0


_CONTEXT_METRICS = {
    **METRIC_PATTERNS,
    "revenue": METRIC_PATTERNS["revenue"] + r"|營收|營業收入|營業額|總收入",
    "net_income": METRIC_PATTERNS["net_income"] + r"|淨利(?:潤)?(?!率)|淨收益",
    "operating_income": METRIC_PATTERNS["operating_income"] + r"|營業利益(?!率)|營業利潤(?!率)",
    "eps_diluted": METRIC_PATTERNS["eps_diluted"] + r"|每股盈餘|每股收益",
    "gross_profit": r"\bgross profit\b|毛利(?!率)",
    "total_assets": r"\b(?:total )?assets\b|總資產",
    "cash": r"\bcash\b|現金",
    "capex": r"\b(?:capex|capital expenditures?)\b|資本支出",
    "rd_expense": r"\b(?:research and development|r&d)\b|研發費用|研發支出",
    "shares_outstanding": r"\b(?:shares outstanding|outstanding shares)\b|流通股數|已發行股份",
    "gross_margin": r"\bgross margin\b|毛利率",
    "operating_margin": r"\boperating margin\b|營業利益率",
    "net_margin": r"\bnet(?: profit)? margin\b|淨利率",
}


def _context_matches(text: str, fact: Mapping) -> bool:
    """A unique number alone must not move a value to another issuer/metric."""
    current = fact.get("current_fact") or fact
    company = {**current, **fact}
    cik = str(company.get("cik") or "").zfill(10)
    company["cik"] = cik
    ticker = str(company.get("ticker") or "")
    ticker_match = ticker and re.search(r"(?<![A-Za-z0-9])(?:\$" + re.escape(ticker) + r"|" + re.escape(ticker) + r")(?![A-Za-z0-9])", text)
    if not name_agrees(text, company) and not ticker_match:
        return False
    if any(name_agrees(text, {"cik": other}) for other in ALIASES if other != cik):
        return False
    metrics = {name for name, pattern in _CONTEXT_METRICS.items() if re.search(pattern, text, re.I)}
    return metrics == {company.get("metric")}


def _number(value: Any) -> Decimal | None:
    if type(value) not in (int, float):
        return None
    parsed = Decimal(str(value))
    return parsed if parsed.is_finite() else None


def _periods(text: str) -> set[str]:
    # The existing EN parser plus explicit Traditional Chinese fiscal/quarter
    # labels. An unqualified Chinese quarter remains calendar, never fiscal.
    periods = claim_periods(text)
    periods.update(re.findall(r"(?<![A-Za-z0-9])(?:FY20\d{2}(?:Q[1-4])?|20\d{2}Q[1-4])(?![A-Za-z0-9])", text.upper()))
    for m in re.finditer(r"(20\d{2})\s*(財年|會計年度|年)?\s*第?([1-4一二三四])季", text):
        q = str("一二三四".index(m[3]) + 1) if m[3] in "一二三四" else m[3]
        periods.discard("FY" + m[1])  # Remove the EN parser's annual fallback.
        periods.add(("FY" if m[2] in {"財年", "會計年度"} else "") + m[1] + "Q" + q)
    return periods


def _filing_url(fact: Mapping, cik: Any) -> str | None:
    url = fact.get("filing_url")
    if isinstance(url, str):
        try:
            parts = urlsplit(url)
            if (parts.scheme == "https" and parts.netloc == "www.sec.gov"
                    and re.fullmatch(r"/Archives/edgar/data/\d+/[\w./-]+", parts.path)
                    and not parts.query and not parts.fragment):
                return url
        except ValueError:
            pass
    accn = str(fact.get("accn") or "")
    if re.fullmatch(r"\d{10}-\d{2}-\d{6}", accn) and re.fullmatch(r"\d{1,10}", str(cik or "")):
        return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn.replace('-', '')}/"
    return None


def _citations(fact: Mapping, evidence_id: str, *, cik=None, unit=None) -> list[dict] | None:
    """Require every leaf, including nested derived quarters in growth checks."""
    cik, unit = fact.get("cik", cik), fact.get("unit", unit)
    if "current_fact" in fact or "base_fact" in fact:
        children = [fact.get("current_fact"), fact.get("base_fact")]
    elif fact.get("components"):
        children = fact["components"]
    elif fact.get("derived"):
        return None
    else:
        url = _filing_url(fact, cik)
        if not url:
            return None
        return [{"evidence_id": evidence_id, "url": url, "form": fact.get("form"),
                 "accn": fact.get("accn"), "value": fact.get("value"), "unit": unit,
                 "period": fact.get("period"), "period_type": fact.get("period_type"),
                 "start": fact.get("start"), "end": fact.get("end")}]
    if not isinstance(children, list) or not children:
        return None
    result = []
    for child in children:
        if not isinstance(child, Mapping):
            return None
        found = _citations(child, evidence_id, cik=cik, unit=unit)
        if found is None:
            return None
        for citation in found:
            if citation not in result:
                result.append(citation)
    return result


def _amount(match: re.Match, unit: str) -> tuple[Decimal, Decimal] | None:
    currency = (match["currency"] or "").strip().upper()
    suffix = match["suffix"] or ""
    suffix = suffix.lower() if suffix.lower() == "shares" else suffix.upper() if suffix.isascii() else suffix
    scale = (match["scale"] or "").lower()
    currencies = {"$": "USD", "US$": "USD", "USD": "USD", "美元": "USD", "美金": "USD",
                  "€": "EUR", "EUR": "EUR", "歐元": "EUR", "£": "GBP", "GBP": "GBP", "英鎊": "GBP",
                  "NT$": "TWD", "TWD": "TWD", "元": "TWD", "新台幣": "TWD", "新臺幣": "TWD",
                  "HK$": "HKD", "HKD": "HKD", "港元": "HKD", "港幣": "HKD", "人民幣": "CNY",
                  "CNY": "CNY", "RMB": "CNY", "C$": "CAD", "CAD": "CAD", "A$": "AUD", "AUD": "AUD", "JPY": "JPY", "¥": "JPY"}
    declared = {currencies[v] for v in (currency, suffix) if v in currencies}
    if len(declared) > 1 or (declared and declared != {unit.split("/")[0]}):
        return None
    percent = scale in {"%", "％", "percent"}
    if percent != (unit in {"%", "percent"}) or (suffix in {"股", "shares"} and unit != "shares"):
        return None
    if unit not in {"USD", "USD/shares", "EUR", "GBP", "TWD", "HKD", "CNY", "shares", "%", "percent"}:
        return None
    if not (currency or suffix or scale):  # Don't mistake a year/quarter for an amount.
        return None
    raw = (match["sign"] or "") + match["number"]
    if len(re.findall(r"[+−-]", raw)) > 1:
        return None
    value = Decimal(raw.replace(",", "").replace("−", "-"))
    multiplier = Decimal(_SCALES.get(scale, 1))
    return value * multiplier, multiplier


def _replacement(match: re.Match, actual: Decimal, scale: Decimal) -> str:
    """Only actual_value supplies digits; preserve the literal scale."""
    raw = match["number"].lstrip("+−-")
    places = len(raw.partition(".")[2])
    # A million/billion mix-up often copies an integer coefficient in the
    # wrong scale. Keep that scale, but do not round the corrected fraction
    # to a whole billion ($164,501 billion -> $164.5 billion). Only an exact
    # thousandfold error enables this extra precision; ordinary edits keep
    # the source's decimal places. Retain at least four significant digits.
    stated = Decimal(raw.replace(",", "")) * scale
    if scale > 1 and actual and stated == abs(actual) * 1000:
        places = max(places, 1, 3 - (abs(actual) / scale).adjusted())
    with localcontext() as ctx:
        ctx.prec = max(28, len(actual.as_tuple().digits) + abs(actual.adjusted()) + places + 16)
        value = (actual / scale).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    if value == 0:
        value = abs(value)  # Avoid a displayed negative zero after rounding.
    digits = format(abs(value), f",.{places}f" if "," in raw else f".{places}f")
    sign = "-" if value < 0 else "+" if "+" in (match["sign"] + match["number"][:1]) else ""
    before = match.string[match.start():match.start("number")]
    if match["sign"]:
        before = sign + before[len(match["sign"]):]
    elif match["currency"]:
        before = sign + before
    else:
        digits = sign + digits
    return before + digits + match.string[match.end("number"):match.end()]


def _occurrences(text: str, phrase: str) -> list[int]:
    return [m.start() for m in re.finditer(re.escape(phrase), text)] if phrase else []


def _sentence(original: str, start: int, end: int) -> str:
    separators = list(re.finditer(r"\.(?!\d)|[!?。！？;；\n]|\b(?:while|whereas|but)\b|[，；]", original, re.I))
    left = max((m.end() for m in separators if m.end() <= start), default=0)
    right = min((m.start() for m in separators if m.start() >= end), default=len(original))
    return original[left:right]


def build_corrections(original: str, checks: Sequence[Mapping], evidence: Sequence[Mapping]) -> dict:
    """Return span-bound edits and explicit reasons for every unedited assertion.

    Model text may help locate a literal span. It cannot supply replacement
    text/numbers, currency, period, citations or a reason for making an edit.
    No input is mutated. Ambiguous/missing context fails closed.
    """
    by_id: dict[str, list[Mapping]] = {}
    for fact in evidence:
        eid = fact.get("evidence_id") or fact.get("id")
        if isinstance(eid, str):
            by_id.setdefault(eid, []).append(fact)
    edits, unchanged = [], []

    def retain(index: int, check: Mapping, reason: str) -> None:
        en, zh = REASONS[reason]
        unchanged.append({"check_index": index, "text": str(check.get("text") or ""),
                          "reason_code": reason, "reason": {"en": en, "zh": zh}})

    for index, check in enumerate(checks):
        verdict = check.get("program_verdict")
        if verdict != "contradicted":
            reason = {"supported": "supported", "unchecked": "not_judged",
                      "insufficient_evidence": "insufficient_evidence"}.get(verdict, "not_contradicted")
            retain(index, check, reason)
            continue
        text = str(check.get("text") or "")
        kind = check.get("claim_type", "value")  # Legacy recorded value checks lack this key.
        if kind not in {"value", "change_pct", "change_abs"} or _QUALITATIVE.search(text):
            retain(index, check, "non_numeric")
            continue
        actual = _number(check.get("actual_value"))
        stated = _number(check.get("stated_value_used", check.get("stated_value")))
        if (check.get("evidence_valid") is not True or actual is None or stated is None
                or check.get("stated_text_unparsed") or check.get("threshold_from_model")):
            retain(index, check, "invalid_evidence")
            continue
        if check.get("period_ambiguous") or check.get("invalid_interpretations") or len(check.get("interpretations") or []) > 1:
            retain(index, check, "ambiguous_period")
            continue
        if check.get("comparator", "eq") not in {"eq", "approx"}:
            retain(index, check, "unsupported_wording")
            continue
        ids = check.get("evidence_ids") or []
        if not ids or any(not isinstance(eid, str) or len(by_id.get(eid, [])) != 1 for eid in ids):
            retain(index, check, "missing_citation")
            continue
        refs = [by_id[eid][0] for eid in dict.fromkeys(ids)]
        field = {"value": "value", "change_pct": "pct_change", "change_abs": "abs_change"}[kind]
        primary = [fact for fact in refs if _number(fact.get(field)) == actual]
        if len(primary) != 1:
            retain(index, check, "ambiguous_evidence")
            continue
        fact = primary[0]
        unit = "%" if kind == "change_pct" else fact.get("unit") or (fact.get("current_fact") or {}).get("unit")
        period = fact.get("period")
        if not isinstance(unit, str) or not isinstance(period, str):
            retain(index, check, "ambiguous_evidence")
            continue
        if ((check.get("unit") and check["unit"] != unit)
                or (check.get("period") and check["period"] != period)):
            retain(index, check, "ambiguous_evidence")
            continue
        citations = []
        for ref in refs:
            found = _citations(ref, str(ref.get("evidence_id") or ref.get("id")))
            if found is None:
                break
            citations.extend(c for c in found if c not in citations)
        else:
            found = citations
        if not found:
            retain(index, check, "missing_citation")
            continue

        anchors = _occurrences(original, text)
        if len(anchors) > 1:
            retain(index, check, "ambiguous_span")
            continue
        low, high = (anchors[0], anchors[0] + len(text)) if anchors else (0, len(original))
        candidates = []
        for match in _AMOUNT.finditer(original, low, high):
            parsed = _amount(match, unit)
            context = original[low:high] if anchors else _sentence(original, match.start(), match.end())
            direction = _direction(context) if kind.startswith("change_") else 0
            if parsed is not None and (parsed[0] == stated or (direction and abs(parsed[0]) == abs(stated))):
                candidates.append((match, parsed[1], context, direction, parsed[0]))
        if len(candidates) != 1:
            retain(index, check, "ambiguous_span" if candidates else "span_not_found")
            continue
        match, scale, context, direction, literal_value = candidates[0]
        periods = _periods(context)
        allowed = {period, fact.get("base_period")} if kind.startswith("change_") else {period}
        if period not in periods or not periods <= allowed:
            retain(index, check, "ambiguous_period")
            continue
        if _QUALITATIVE.search(context):
            retain(index, check, "non_numeric")
            continue
        if _RANGE_OR_COMPOUND.search(context):
            retain(index, check, "unsupported_wording")
            continue
        if not _context_matches(context, fact):
            retain(index, check, "ambiguous_context")
            continue
        if direction and (direction == 2 or literal_value < 0 or actual * direction <= 0):
            retain(index, check, "unsupported_wording")
            continue
        replacement = _replacement(match, abs(actual) if direction else actual, scale)
        if replacement == match[0]:
            retain(index, check, "unsupported_wording")
            continue
        edits.append({"check_index": index, "start": match.start(), "end": match.end(),
                      "original": match[0], "replacement": replacement,
                      "actual_value": check["actual_value"], "unit": unit, "period": period,
                      "base_period": fact.get("base_period"), "evidence_ids": list(dict.fromkeys(ids)),
                      "citations": citations})

    # Reject *all* overlapping proposals rather than picking a winner by order.
    conflicts = {e["check_index"] for e in edits for other in edits
                 if e is not other and e["start"] < other["end"] and other["start"] < e["end"]}
    for index in sorted(conflicts):
        retain(index, checks[index], "overlapping_spans")
    return {"label": dict(LABEL), "original_text": original, "span_unit": "unicode_codepoints",
            "edits": sorted((e for e in edits if e["check_index"] not in conflicts), key=lambda e: e["start"]),
            "not_corrected": sorted(unchanged, key=lambda item: item["check_index"])}
