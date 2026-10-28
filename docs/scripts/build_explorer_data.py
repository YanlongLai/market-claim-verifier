"""Build the compact JSON behind docs/explorer/index.html from an eval run directory.

Usage: .venv/bin/python docs/scripts/build_explorer_data.py [--eval DIR] [--claims FILE] [--out FILE]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEMS = ["single_shot@meta", "agent@meta", "single_shot@baseten", "agent@baseten", "single_shot@fireworks", "agent@fireworks"]
EVIDENCE_KEYS = ("ticker", "entity", "metric", "concept", "value", "unit", "start", "end", "form", "filed", "accn",
                 "frame", "fiscal_year", "fiscal_period", "derived", "filing_url", "period", "period_basis")


def _evidence(trace: dict, cited: set[str]) -> list[dict]:
    rows = []
    for call in trace.get("tool_calls") or []:
        result = call.get("result")
        if not isinstance(result, dict):
            continue
        ev_id = result.get("evidence_id")
        if ev_id is None or ev_id not in cited:
            continue
        row = {key: result.get(key) for key in EVIDENCE_KEYS if result.get(key) is not None}
        row["id"] = ev_id
        row["tool"] = call.get("name")
        if call.get("name") == "compute_change":
            row.update({k: result.get(k) for k in ("change_pct", "current", "previous", "direction") if k in result})
        prov = result.get("provenance") or {}
        row["tier"] = prov.get("tier")
        row["strength"] = prov.get("strength")
        row["restated"] = prov.get("restated")
        rows.append(row)
    return rows


def build(eval_dir: Path, claims_path: Path) -> dict:
    claims = [json.loads(line) for line in claims_path.read_text().splitlines() if line.strip()]
    summary = json.loads((eval_dir / "summary.json").read_text())
    out_claims = []
    for claim in claims:
        item = {
            "id": claim["id"], "layer": claim.get("layer"), "family": claim.get("family"), "split": claim.get("split"),
            "claim": claim["claim"], "gold": claim["gold_verdict"], "gold_note": claim.get("gold_note"),
            "source": claim.get("source"), "gold_correction": claim.get("gold_correction"), "results": {},
        }
        for key in ("source_url", "source_title", "source_tier", "source_domain", "published"):
            if claim.get(key):
                item.setdefault("source", {}) if item["source"] is None else None
                item["source"] = {**(item["source"] or {}), key: claim[key]}
        for system in SYSTEMS:
            path = eval_dir / f"{claim['id']}--{system}.json"
            if not path.exists():
                continue
            pair = json.loads(path.read_text())
            res = {
                "verdict": pair.get("verdict"), "status": pair.get("status"),
                "cost": round(float(pair.get("cost_usd") or 0), 5), "latency_s": round((pair.get("latency_ms") or 0) / 1000, 1),
                "summary": (pair.get("summary") or "")[:400], "strength": pair.get("evidence_strength"),
            }
            if system.startswith("agent@"):
                checks = []
                cited: set[str] = set()
                for sub in pair.get("program_checks") or []:
                    cited.update(sub.get("evidence_ids") or [])
                    checks.append({k: sub.get(k) for k in (
                        "text", "stated_value_used", "actual_value", "tolerance", "comparator", "model_comparator",
                        "comparator_corrected", "program_verdict", "reason", "period_ambiguous", "evidence_ids",
                        "evidence_summary") if sub.get(k) is not None})
                res["checks"] = checks
                trace_path = pair.get("trace_path")
                if trace_path and (eval_dir / trace_path).exists():
                    res["evidence"] = _evidence(json.loads((eval_dir / trace_path).read_text()), cited)
            item["results"][system] = res
        out_claims.append(item)
    keep = ("confidence_intervals", "paired_comparisons", "source_scorecard", "system_totals", "provider_comparison")
    stats = {key: summary.get(key) for key in keep}
    for pair in (stats.get("paired_comparisons") or {}).values():
        pair.pop("claim_ids", None)
    return {"run": str(eval_dir.relative_to(ROOT)), "claims": out_claims, "stats": stats}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval", default="docs/evidence/eval-v2-2026-10-27")
    parser.add_argument("--claims", default="eval/v2/claims-v2-corrected.jsonl")
    parser.add_argument("--out", default="docs/explorer/data.json")
    args = parser.parse_args()
    data = build(ROOT / args.eval, ROOT / args.claims)
    out = ROOT / args.out
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(out, out.stat().st_size, "bytes", len(data["claims"]), "claims")


if __name__ == "__main__":
    main()
