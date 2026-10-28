#!/usr/bin/env python3
"""Build the small, reader-facing data snapshot used by docs/site.

The explorer data is intentionally much richer than the landing page needs. This
script extracts only the values and three concrete examples rendered on the site,
so the page can be refreshed after a new evaluation without copying numbers by hand.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXPLORER_PATH = ROOT / "docs" / "explorer" / "data.json"
SUMMARY_PATH = ROOT / "docs" / "evidence" / "eval-v2-2026-10-27" / "summary.json"
OUTPUT_PATH = ROOT / "docs" / "site" / "data" / "site.json"

SYSTEM_ORDER = [
    "agent@baseten",
    "agent@fireworks",
    "agent@meta",
    "single_shot@meta",
    "single_shot@baseten",
    "single_shot@fireworks",
]

SYSTEM_META = {
    "agent@baseten": {"mode": "agent", "provider": "Baseten", "short": "Agent · Baseten"},
    "agent@fireworks": {"mode": "agent", "provider": "Fireworks", "short": "Agent · Fireworks"},
    "agent@meta": {"mode": "agent", "provider": "Meta API", "short": "Agent · Meta API"},
    "single_shot@meta": {"mode": "single-shot", "provider": "Meta API", "short": "Single-shot · Meta API"},
    "single_shot@baseten": {"mode": "single-shot", "provider": "Baseten", "short": "Single-shot · Baseten"},
    "single_shot@fireworks": {"mode": "single-shot", "provider": "Fireworks", "short": "Single-shot · Fireworks"},
}

EXAMPLE_IDS = ["G0144", "G0235", "G0193"]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def round_points(value: float) -> int:
    return int(round(value * 100))


def system_snapshot(system_id: str, stats: dict[str, Any]) -> dict[str, Any]:
    overall = stats["confidence_intervals"][system_id]["overall"]
    totals = stats["system_totals"][system_id]
    meta = SYSTEM_META[system_id]
    return {
        "id": system_id,
        **meta,
        "n": overall["n"],
        "correct": overall["correct"],
        "accuracy": overall["accuracy"],
        "accuracy_ci": {
            "lower": overall["accuracy_ci"]["lower"],
            "upper": overall["accuracy_ci"]["upper"],
        },
        "false_supported": overall["false_supported"],
        "false_supported_denominator": overall["harmful_gold"],
        "cost_mean": totals["cost_usd"]["mean"],
        "latency_mean_s": totals["latency_ms"]["mean"] / 1000,
    }


def evidence_snapshot(item: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "ticker",
        "entity",
        "metric",
        "value",
        "unit",
        "form",
        "period",
        "period_basis",
        "tier",
        "strength",
        "derived",
        "restated",
    )
    return {key: item.get(key) for key in fields if key in item}


def example_snapshot(claim: dict[str, Any]) -> dict[str, Any]:
    agent = claim["results"]["agent@baseten"]
    checks = agent.get("checks") or []
    evidence = agent.get("evidence") or []
    first_check = checks[0] if checks else {}
    return {
        "id": claim["id"],
        "family": claim["family"],
        "claim": claim["claim"],
        "gold": claim["gold"],
        "single_shot_verdict": claim["results"]["single_shot@meta"].get("verdict"),
        "agent_verdict": agent.get("verdict"),
        "program_reason": first_check.get("reason"),
        "period_ambiguous": first_check.get("period_ambiguous", False),
        "evidence_summary": first_check.get("evidence_summary"),
        "evidence": [evidence_snapshot(item) for item in evidence],
    }


def family_snapshot(stats: dict[str, Any], family: str) -> dict[str, Any]:
    selected = {}
    for system_id in ("agent@meta", "agent@baseten", "agent@fireworks"):
        family_stats = stats["confidence_intervals"][system_id]["family"][family]
        selected[system_id] = {
            "correct": family_stats["correct"],
            "n": family_stats["n"],
            "accuracy": family_stats["accuracy"],
        }
    return {"id": family, "systems": selected}


def main() -> None:
    explorer = read_json(EXPLORER_PATH)
    stats = explorer["stats"]
    summary = read_json(SUMMARY_PATH) if SUMMARY_PATH.exists() else {}
    claims = {claim["id"]: claim for claim in explorer["claims"]}

    paired = {}
    pair_ids = {
        "meta": "agent@meta_vs_single_shot@meta",
        "baseten": "agent@baseten_vs_single_shot@baseten",
        "fireworks": "agent@fireworks_vs_single_shot@fireworks",
    }
    for provider, pair_id in pair_ids.items():
        comparison = stats["paired_comparisons"][pair_id]
        paired[provider] = {
            "points": round_points(comparison["accuracy_difference"]),
            "mcnemar_exact_p": comparison["mcnemar_exact_p"],
            "n": comparison["n"],
        }

    generated_at = summary.get("generated_at", "")
    output = {
        "eval": {
            "claim_count": len(explorer["claims"]),
            "result_count": summary.get("result_count", len(explorer["claims"]) * len(SYSTEM_ORDER)),
            "generated_at": generated_at,
            "run": explorer.get("run"),
        },
        "systems": [system_snapshot(system_id, stats) for system_id in SYSTEM_ORDER],
        "paired": paired,
        "families": [
            family_snapshot(stats, "record_first"),
            family_snapshot(stats, "yoy"),
            family_snapshot(stats, "period_trap"),
        ],
        "examples": [example_snapshot(claims[claim_id]) for claim_id in EXAMPLE_IDS],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
