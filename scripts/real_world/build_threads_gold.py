"""Independent, offline SEC gold for the frozen Threads paraphrases.

Only standard-library source parsing and Decimal comparisons. No claimcheck
imports, inferred reporting years, provider calls or output-dependent labels.
The primary_release basis name is retained for phase-1 metric compatibility;
the tier and source_kind distinguish companyfacts from issuer releases.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path

from build_gold import normalized


class Sources:
    def __init__(self, out):
        self.out = out
        self.manifest = json.loads((out / "sources/manifest.json").read_text())

    def raw(self, ticker, kind):
        row = next(r for r in self.manifest if r["ticker"] == ticker and r["kind"] == kind)
        raw = gzip.decompress((self.out / "sources" / row["gzip_file"]).read_bytes())
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("primary source hash mismatch")
        return row, raw

    def fact(self, ticker, tag, start, end):
        source, raw = self.raw(ticker, "companyfacts")
        data = json.loads(raw)["facts"]["us-gaap"][tag]["units"]["USD"]
        candidates = [(i, row) for i, row in enumerate(data) if row.get("start") == start and row["end"] == end
                      and row.get("filed", "9999") <= "2026-11-02" and row.get("form") in {"10-K", "10-Q"}]
        if not candidates:
            raise ValueError("no exact primary period")
        latest = max(row["filed"] for _, row in candidates)
        candidates = [(i, row) for i, row in candidates if row["filed"] == latest]
        if len({str(row["val"]) for _, row in candidates}) != 1:
            raise ValueError("conflicting primary facts require review")
        index, row = candidates[0]
        return {"source": source, "source_kind": "companyfacts", "tier": "L1",
                "json_pointer": f"/facts/us-gaap/{tag}/units/USD/{index}", "fact": row,
                "reference_value": str(row["val"])}

    def release(self, ticker, pattern, anchor, scale="1"):
        source, raw = self.raw(ticker, "release")
        text = normalized(raw)
        matches = list(re.finditer(pattern, text, re.I))
        if len(matches) != 1 or anchor not in text:
            raise ValueError(f"ambiguous/missing release anchor: {ticker}: {pattern}")
        m = matches[0]
        return {"source": source, "source_kind": "issuer_release", "tier": "L4",
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "match_span": [m.start(), m.end()],
                "match_text": m[0], "period_anchor": anchor, "regex": pattern, "scale": scale,
                "reference_value": str(Decimal(m["value"].replace(",", "")) * Decimal(scale))}


def compare(reference, claimed, tolerance, metric):
    value, claim, half = map(Decimal, (reference["reference_value"], claimed, tolerance))
    return {**reference, "claimed_value": claimed, "rounding_half_unit": tolerance, "metric": metric,
            "verdict": "supported" if abs(value - claim) <= half else "contradicted"}


def build(out):
    if (out / "FREEZE.json").exists():
        raise RuntimeError("gold frozen; use a separately named recheck")
    sources = Sources(out)
    components = {}
    rev = "RevenueFromContractWithCustomerExcludingAssessedTax"
    a = sources.fact("GOOG", "Revenues", "2026-07-01", "2026-09-30")
    b = sources.fact("GOOG", "Revenues", "2025-07-01", "2025-09-30")
    growth = (Decimal(a["reference_value"]) / Decimal(b["reference_value"]) - 1) * 100
    components["T02"] = [compare(a, "127600000000", "50000000", "Q3 2026 revenue"),
                         compare({"reference_value": str(growth), "inputs": [a, b], "formula": "(current/prior - 1)*100", "tier": "L1"}, "25", "0.5", "year-over-year revenue growth")]
    components["T03"] = [compare(sources.fact("CRWV", rev, f"{year}-01-01", f"{year}-12-31"), value, tolerance, f"{year} annual revenue")
                         for year, value, tolerance in [(2023, "2290000000", "5000000"), (2024, "1915000000", "500000"), (2025, "51310000000", "5000000")]]
    components["T03"].append(compare(sources.fact("CRWV", rev, "2026-01-01", "2026-03-31"), "4653000000", "500000", "2026 Q1 revenue"))
    sndk_anchor = "First Quarter 2027 Financial Results"
    components["T09"] = [
        compare(sources.fact("SNDK", rev, "2026-07-04", "2026-10-02"), "11000000000", "50000000", "FY2027 Q1 revenue"),
        compare(sources.release("SNDK", r"Q1 2027 Q1 2026 Y/Y Q1 2027 Q1 2026 Y/Y Revenue \$11,031 \$2,308 up (?P<value>378)%", sndk_anchor), "23", "0.5", "year-over-year revenue growth"),
        compare(sources.release("SNDK", r"First quarter Non-GAAP diluted net income per share was \$(?P<value>49\.51)", sndk_anchor), "49.51", "0.005", "adjusted diluted EPS"),
    ]
    amd_anchor = "second quarter 2026"
    components["T19"] = [
        compare(sources.fact("AMD", rev, "2026-03-29", "2026-06-27"), "11540000000", "5000000", "FY2026 Q2 revenue"),
        compare(sources.release("AMD", r"Revenue increased (?P<value>50)% year-over-year", amd_anchor), "50", "0.5", "year-over-year revenue growth"),
        compare(sources.release("AMD", r"net income was \$2\.8 billion and diluted earnings per share was \$(?P<value>1\.66)", amd_anchor), "1.66", "0.005", "non-GAAP diluted EPS"),
        compare(sources.release("AMD", r"Data Center segment revenue was \$(?P<value>6\.7) billion", amd_anchor, "1000000000"), "6700000000", "50000000", "Data Center segment revenue"),
        compare(sources.release("AMD", r"For the third quarter of 2026, AMD expects revenue to be approximately \$(?P<value>13) billion", amd_anchor, "1000000000"), "13000000000", "50000000", "Q3 2026 revenue guidance midpoint; statement, not forecast realization"),
    ]
    apple_anchor = "September 26, 2026"
    components["T33"] = [
        compare(sources.release("AAPL", r"Total net sales \(1\) (?P<value>114,477) 102,466 478,834 416,161", apple_anchor, "1000000"), "114480000000", "5000000", "FY2026 Q4 revenue"),
        compare(sources.release("AAPL", r"quarterly revenue of \$114\.5 billion, up (?P<value>12) percent year over year", apple_anchor), "12", "0.5", "year-over-year revenue growth"),
        compare(sources.release("AAPL", r"Diluted earnings per share was \$(?P<value>2\.10)", apple_anchor), "2.10", "0.005", "diluted EPS"),
        compare(sources.release("AAPL", r"iPhone \$ (?P<value>57,583) \$ 49,025", apple_anchor, "1000000"), "575800000000", "50000000", "FY2026 Q4 iPhone revenue"),
        compare(sources.release("AAPL", r"Greater China (?P<value>17,539) 14,493", apple_anchor, "1000000"), "175400000000", "50000000", "FY2026 Q4 Greater China revenue"),
    ]
    rows, review = [], []
    for case in map(json.loads, (out / "claims.jsonl").read_text().splitlines()):
        id = case["id"]
        row = {"id": id, "claim_sha256": hashlib.sha256(case["claim"].encode()).hexdigest(),
               "gold_verdict": None, "gold_basis": "review_required", "factual_truth": "unresolved"}
        if id in components:
            checked = components[id]
            verdict = "contradicted" if any(c["verdict"] == "contradicted" for c in checked) else "supported"
            row.update(gold_verdict=verdict, gold_basis="primary_release", components=checked,
                       tier=sorted({c["tier"] for c in checked}), factual_truth="refuted" if verdict == "contradicted" else "confirmed",
                       note="Compound assertion: one independently refuted component suffices for contradicted. Support requires all material assertions checked. Source tier is not an audit of issuer accounts.")
            if id == "T03":
                row["note"] += " 2022 is absent from the saved companyfacts snapshot; the other explicit-year contradictions suffice. Q1 value is actually the six-month total."
            if id == "T33":
                row["note"] += " Revenue/EPS/growth agree with the release at stated precision; iPhone and Greater China numbers are about ten times source values."
        elif case["sample_group"] == "support_control":
            row.update(gold_verdict="insufficient_evidence", gold_basis="scope_policy", tier=None,
                       note="Expected abstention/skip for prices, opinions, anecdotes, ownership trades, private-company or non-US filing domain. Financial truth unscored; no claim that all such events are intrinsically unverifiable.")
        else:
            row["note"] = "Reporting year/period, issuer context or financial basis missing. Do not infer from post date, matching values or latest filing. Independent primary truth remains unresolved."
            if id == "N07":
                row["note"] = "Collector expected out of scope, but buyback authorizations can appear in SEC releases. No authorization dates are stated, so retain for review rather than force a scope label."
            if id in {"O02", "O20"}:
                row["note"] += " Financing/backlog requires a dated release and precise instrument/metric definition."
        rows.append(row)
        if row["gold_basis"] == "review_required":
            review.append(f"| {id} | {case['claim']} | {row['note']} |")
    (out / "gold.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows))
    (out / "GOLD_REVIEW.md").write_text("# Threads gold review list\n\nFrozen before paid execution; no independent Claude review is claimed. Missing years remain missing. Scope-policy gold measures abstention and does not establish financial truth. No corrections to the collector's shown numbers.\n\n| ID | Paraphrase | Review required |\n|---|---|---|\n" + "\n".join(review) + "\n\nN07 is deliberately a review item despite its collector N identifier. Explicit-year SEC cases: T02, T03, T09, T19, T33. T09 has a year-over-year versus sequential-growth mismatch. T03 and T33 include confirmed displayed-number discrepancies; translation causation requires the original-language post.\n")
    media = [{"id": id, "gold_basis": "review_required", "gold_verdict": None, "factual_truth": "unresolved",
              "human_visual_review_before_ocr": True, "paraphrase": text,
              "scope_components": "Price levels, changes, moving averages, sector returns and commentary are outside the SEC financial checker.",
              "note": "No OCR/ASR truth label or financial-accuracy denominator; media overlaps two own posts. Missing reporting period or financing detail requires review."}
             for id, text in [("M01", "Card pairs Tesla's $394.59 quote (+6.01%) with SPCX at $149.21 (+1.17%); it describes SpaceX completing $40 billion of debt financing for AI chips and comments on market technicals."),
                              ("M02", "Card pairs Nvidia at $215.56 (+2.18%) with Alphabet at $316.43 (-0.27%); it discusses GPU rental-price increases, $514 billion of Alphabet cloud orders, an upcoming third-quarter release and market technicals.")]]
    (out / "media-gold.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in media))
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    from collections import Counter
    print(dict(Counter(r["gold_basis"] for r in build(parser.parse_args().out))))
