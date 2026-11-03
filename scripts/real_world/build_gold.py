"""Independent news gold: primary release anchors, scope labels and review gaps.

Uses only the standard library, not claimcheck's retrieval parsers or verdict code.
Absence of a period is never repaired using a publication date or matching value.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, value):
        self.parts.append(value)


def normalized(raw: bytes) -> str:
    parser = Text()
    parser.feed(raw.decode("utf-8"))
    return re.sub(r"\s+", " ", " ".join(parser.parts))


REFERENCES = {
    "RW006": {
        "file": "UNH-ex99.1.html", "period": "FY2026", "metric": "adjusted_eps_guidance_minimum",
        "pattern": r"full year 2026 adjusted net earnings of at least \$(?P<value>\d+\.\d+) per share",
        "anchor": "raised guidance for full year 2026", "claimed": "20.50", "scale": "1", "rounding": "0",
        "note": "Confirms that management stated this minimum; does not verify realization of the forecast. The minimum comparator is preserved.",
    },
    "RW026": {
        "file": "ARCC-ex99.1.html", "period": "2026Q3", "metric": "total_investment_income",
        "pattern": r"Total investment income (?P<value>[\d,]+) 782 2,294 2,259",
        "anchor": "third quarter ended September 30, 2026", "claimed": "763000000", "scale": "1000000", "rounding": "500000",
        "note": "First table column is Q3 2026; total investment income, not net investment income or consolidated GAAP sales.",
    },
    "RW050": {
        "file": "SHEL-quarterlyexhibit992-q32026.htm", "period": "2026Q3", "metric": "income_attributable_to_shareholders",
        "pattern": r"Q3 2026 Q2 2026 Q3 2025 Reference\* 2026 2025 (?P<value>[\d,]+) 10,821 5,322 Income attributable to Shell plc shareholders",
        "anchor": "3 rd QUARTER 2026 AND NINE MONTHS UNAUDITED RESULTS", "claimed": "12100000000", "scale": "1000000", "rounding": "50000000",
        "note": "$12,057m rounds to $12.1bn. Total income for the period ($12,145m) also rounds to $12.1bn; the net-income definition does not change this rounded comparison. SEC 6-K issuer release is outside the current agent's 8-K discovery path.",
    },
    "RW052": {
        "file": "SBUX-ex99.1.html", "period": "FY2026Q4", "metric": "us_comparable_coffeehouse_sales_growth",
        "pattern": r"Q4 Fiscal Year 2026 Highlights.*?U\.S\. comparable coffeehouse sales increased (?P<value>\d+\.\d+)%",
        "anchor": "Q4 Fiscal Year 2026 Highlights", "claimed": "7.7", "scale": "1", "rounding": "0.05",
        "note": "US comparable coffeehouse sales, not global sales, North America sales, total revenue or a consolidated GAAP growth metric.",
    },
}


def primary(reference: dict, raw: bytes) -> dict:
    text = normalized(raw)
    matches = list(re.finditer(reference["pattern"], text, re.I))
    if len(matches) != 1 or reference["anchor"] not in text:
        raise ValueError("primary source anchor missing or ambiguous")
    match = matches[0]
    value = Decimal(match["value"].replace(",", "")) * Decimal(reference["scale"])
    claimed, rounding = Decimal(reference["claimed"]), Decimal(reference["rounding"])
    return {
        "gold_verdict": "supported" if abs(value - claimed) <= rounding else "contradicted",
        "reference_value": str(value), "claimed_value": str(claimed), "rounding_half_unit": str(rounding),
        "period": reference["period"], "metric": reference["metric"], "note": reference["note"],
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "text_normalization": "HTMLParser.handle_data joined by spaces; whitespace collapsed",
        "match_span": [match.start(), match.end()], "match_text": match[0], "period_anchor": reference["anchor"],
    }


def build(out: Path) -> list[dict]:
    if (out / "FREEZE.json").exists():
        raise RuntimeError("gold is frozen; never overwrite it")
    claims = [json.loads(line) for line in (out / "claims.jsonl").read_text().splitlines()]
    sources = {row["file"]: row for row in json.loads((out / "sources/manifest.json").read_text())}
    rows = []
    for claim in claims:
        row = {"id": claim["id"], "claim_sha256": hashlib.sha256(claim["claim"].encode()).hexdigest(),
               "factual_truth": "unresolved", "gold_verdict": None, "gold_basis": "review_required"}
        if claim["id"] in REFERENCES:
            ref = REFERENCES[claim["id"]]
            source = sources[ref["file"]]
            raw = gzip.decompress((out / "sources" / source["gzip_file"]).read_bytes())
            if hashlib.sha256(raw).hexdigest() != source["sha256"]:
                raise ValueError("primary snapshot hash mismatch")
            checked = primary(ref, raw)
            row.update(checked, gold_basis="primary_release", tier="L4", source=source,
                       factual_truth="confirmed" if checked["gold_verdict"] == "supported" else "refuted")
        elif claim["market"] == "tw":
            row.update(gold_verdict="insufficient_evidence", gold_basis="scope_policy", tier=None,
                       note="TW-listed company/TWD financials require Taiwan primary filings. US SEC retrieval does not validate this statement; this is expected abstention, not a truth label.")
        elif claim["sample_group"] == "support_control":
            row.update(gold_verdict="insufficient_evidence", gold_basis="scope_policy", tier=None,
                       note="Price/opinion/ownership/event/market-share statement is outside the current financial-filing checker. Expected abstention or post skip; factual truth unscored.")
        elif claim["claim_type"] == "analyst_forecast":
            row.update(gold_verdict="insufficient_evidence", gold_basis="scope_policy", tier=None,
                       note="Third-party consensus/forecast changes require a dated analyst-estimate dataset. Issuer guidance cannot independently verify analyst estimates; factual truth unscored.")
        else:
            row["note"] = "Missing reporting year/period, financial basis, or metric definition. Do not infer it from publication date, a matching source value or latest SEC filing. Claude/Owner review required."
            if claim["id"] == "RW002":
                row["note"] += " The word grew does not identify the measured AWS metric."
            if claim["id"] in {"RW019", "RW034"}:
                row["note"] += " Confirm issuer identity/public filing availability."
        rows.append(row)
    (out / "gold.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))
    review = ["# Claude / Owner review before factual scoring", "",
              "Frozen before model execution. No independent Claude review is claimed. A scope-policy verdict is an expected abstention, not confirmation that the news is true or false. Never edit this run's frozen gold in place; add a separately named reviewed-gold recheck.", "",
              "## Ambiguous US financial claims", "", "| ID | Paraphrase | Review needed |", "|---|---|---|"]
    for claim, row in zip(claims, rows):
        if row["gold_basis"] == "review_required":
            review.append(f"| {claim['id']} | {claim['claim']} | {row['note']} |")
    review += ["", "## Scope-only gold", "", "These items have an operational expected outcome only; their financial truth has not been independently established:", ""]
    review += [f"- {row['id']}: {row['note']}" for row in rows if row["gold_basis"] == "scope_policy"]
    review += ["", "TW follow-up requires MOPS/TWSE issuer records and careful ROC-year/currency/quarter alignment. Some stories repeat the same company's metric; story rows are not independent facts. The Lite-On EPS paraphrases retain both 3.27 and 3.28 from different published summaries, without choosing one. Several feed tickers refer to a different company from the statement; metadata tickers are not passed as authenticated issuer context.", ""]
    (out / "GOLD_REVIEW.md").write_text("\n".join(review))
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    rows = build(args.out)
    from collections import Counter
    print(dict(Counter(row["gold_basis"] for row in rows)))
