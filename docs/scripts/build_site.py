#!/usr/bin/env python3
"""Build the small data snapshot used by the reader-facing site.

The landing page only needs a few evaluation values and two real post reports.
Keeping the extraction here means the page never has to copy a claim, span,
verdict, filing value, or URL by hand.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXPLORER_PATH = ROOT / "docs" / "explorer" / "data.json"
SUMMARY_PATH = ROOT / "docs" / "evidence" / "eval-v2-2026-10-27" / "summary.json"
OUTPUT_PATH = ROOT / "docs" / "site" / "data" / "site.json"

EXAMPLE_REPORTS = {
    "en": ROOT / "docs" / "evidence" / "posts-2026-10-28" / "bigtech-thread-baseten" / "report.json",
    "zh": ROOT / "docs" / "evidence" / "posts-2026-10-28" / "tw-social-post-meta" / "report.json",
}

EXAMPLE_IDS = {
    "en": "bigtech-thread-baseten",
    "zh": "tw-social-post-meta",
}

SYSTEM_ORDER = [
    "agent@baseten",
    "agent@fireworks",
    "agent@meta",
    "single_shot@meta",
    "single_shot@baseten",
    "single_shot@fireworks",
]

PROVIDER_ORDER = ("meta", "baseten", "fireworks")

SYSTEM_META = {
    "agent@baseten": {"mode": "agent", "provider": "Baseten", "short": "Agent · Baseten"},
    "agent@fireworks": {"mode": "agent", "provider": "Fireworks", "short": "Agent · Fireworks"},
    "agent@meta": {"mode": "agent", "provider": "Meta API", "short": "Agent · Meta API"},
    "single_shot@meta": {"mode": "single-shot", "provider": "Meta API", "short": "Single-shot · Meta API"},
    "single_shot@baseten": {"mode": "single-shot", "provider": "Baseten", "short": "Single-shot · Baseten"},
    "single_shot@fireworks": {"mode": "single-shot", "provider": "Fireworks", "short": "Single-shot · Fireworks"},
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def display_value(value: Any, unit: str | None) -> str | None:
    """Make a compact display string without changing the stored raw value."""
    if not is_number(value):
        return None
    amount = float(value)
    if unit == "USD":
        sign = "-" if amount < 0 else ""
        absolute = abs(amount)
        if absolute >= 1_000_000_000:
            return f"{sign}${absolute / 1_000_000_000:,.3f}B"
        if absolute >= 1_000_000:
            return f"{sign}${absolute / 1_000_000:,.3f}M"
        return f"{sign}${absolute:,.0f}"
    if unit in {"percent", "%"}:
        return f"{amount:,.3f}%"
    return f"{amount:,.3f}"


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
        "concept",
        "value",
        "unit",
        "start",
        "end",
        "form",
        "filed",
        "accn",
        "frame",
        "fiscal_year",
        "fiscal_period",
        "period",
        "filing_url",
        "id",
        "tier",
    )
    snapshot = {key: item.get(key) for key in fields if key in item}
    if is_number(item.get("value")):
        snapshot["display_value"] = display_value(item["value"], item.get("unit"))
    return snapshot


def first_form(evidence: list[dict[str, Any]]) -> str | None:
    for item in evidence:
        if item.get("form"):
            return item["form"]
    return None


def first_filed(evidence: list[dict[str, Any]]) -> str | None:
    for item in evidence:
        if item.get("filed"):
            return item["filed"]
    return None


def first_url(evidence: list[dict[str, Any]]) -> str | None:
    for item in evidence:
        if item.get("filing_url"):
            return item["filing_url"]
    return None


def source_snapshot(claim: dict[str, Any]) -> dict[str, Any] | None:
    evidence = claim.get("evidence") or []
    for item in evidence:
        if is_number(item.get("value")):
            return {
                "kind": "direct",
                "value": item.get("value"),
                "unit": item.get("unit"),
                "display_value": display_value(item.get("value"), item.get("unit")),
                "form": item.get("form"),
                "filed": item.get("filed"),
                "filing_url": item.get("filing_url"),
                "period": item.get("period"),
            }

    checks = claim.get("program_checks") or []
    if any(is_number(check.get("actual_value")) for check in checks):
        return {
            "kind": "derived",
            "summary": claim.get("summary"),
            "form": first_form(evidence),
            "filed": first_filed(evidence),
            "filing_url": first_url(evidence),
        }
    return None


def claim_snapshot(claim: dict[str, Any]) -> dict[str, Any]:
    evidence = claim.get("evidence") or []
    return {
        "index": claim.get("index"),
        "quote": claim.get("quote"),
        "span": claim.get("span"),
        "claim": claim.get("claim"),
        "ticker": claim.get("ticker"),
        "kind": claim.get("kind"),
        "status": claim.get("status"),
        "verdict": claim.get("verdict"),
        "summary": claim.get("summary"),
        "source": source_snapshot(claim),
        "evidence": [evidence_snapshot(item) for item in evidence],
    }


def example_snapshot(example_id: str, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": example_id,
        "post": report.get("post", ""),
        "provider": report.get("provider"),
        "model": report.get("model"),
        "proposed_count": report.get("proposed_count"),
        "counts": report.get("counts", {}),
        "verdicts": report.get("verdicts", {}),
        "claims": [claim_snapshot(claim) for claim in report.get("claims", [])],
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


def paired_snapshot(stats: dict[str, Any]) -> dict[str, Any]:
    pairs = {
        "meta": "agent@meta_vs_single_shot@meta",
        "baseten": "agent@baseten_vs_single_shot@baseten",
        "fireworks": "agent@fireworks_vs_single_shot@fireworks",
    }
    paired = {}
    for provider, pair_id in pairs.items():
        comparison = stats["paired_comparisons"][pair_id]
        paired[provider] = {
            "points": round_points(comparison["accuracy_difference"]),
            "mcnemar_exact_p": comparison["mcnemar_exact_p"],
            "n": comparison["n"],
        }
    return paired


def chart_snapshot(systems: dict[str, dict[str, Any]], paired: dict[str, Any]) -> list[dict[str, Any]]:
    chart = []
    for provider in PROVIDER_ORDER:
        without = systems[f"single_shot@{provider}"]
        with_checks = systems[f"agent@{provider}"]
        chart.append(
            {
                "id": provider,
                "provider": with_checks["provider"],
                "without": {
                    "accuracy": without["accuracy"],
                    "percent": round_points(without["accuracy"]),
                },
                "with_checks": {
                    "accuracy": with_checks["accuracy"],
                    "percent": round_points(with_checks["accuracy"]),
                },
                "change_points": paired[provider]["points"],
            }
        )
    return chart


def research_snapshot(systems: dict[str, dict[str, Any]], paired: dict[str, Any], families: list[dict[str, Any]]) -> dict[str, Any]:
    confidence_intervals = {}
    cost_latency = {}
    for provider in PROVIDER_ORDER:
        without = systems[f"single_shot@{provider}"]
        with_checks = systems[f"agent@{provider}"]
        confidence_intervals[provider] = {
            "without": without["accuracy_ci"],
            "with_checks": with_checks["accuracy_ci"],
        }
        cost_latency[provider] = {
            "without": {
                "cost_mean": without["cost_mean"],
                "latency_mean_s": without["latency_mean_s"],
            },
            "with_checks": {
                "cost_mean": with_checks["cost_mean"],
                "latency_mean_s": with_checks["latency_mean_s"],
            },
        }
    return {
        "confidence_intervals": confidence_intervals,
        "paired": paired,
        "cost_latency": cost_latency,
        "families": families,
        "gold_corrections": [
            "Amazon's 12-month 10-Q value was trailing-twelve-month data, not a fiscal year.",
            "Apple's 52/53-week quarter ending 2023-07-01 belongs to calendar Q2, not Q3.",
        ],
    }


def main() -> None:
    explorer = read_json(EXPLORER_PATH)
    stats = explorer["stats"]
    summary = read_json(SUMMARY_PATH) if SUMMARY_PATH.exists() else {}

    systems = {system_id: system_snapshot(system_id, stats) for system_id in SYSTEM_ORDER}
    paired = paired_snapshot(stats)
    families = [
        family_snapshot(stats, "record_first"),
        family_snapshot(stats, "yoy"),
        family_snapshot(stats, "period_trap"),
    ]

    output = {
        "eval": {
            "claim_count": len(explorer["claims"]),
            "result_count": summary.get("result_count", len(explorer["claims"]) * len(SYSTEM_ORDER)),
            "generated_at": summary.get("generated_at", ""),
            "run": explorer.get("run"),
        },
        "systems": list(systems.values()),
        "chart": chart_snapshot(systems, paired),
        "paired": paired,
        "families": families,
        "research": research_snapshot(systems, paired, families),
        "examples": {
            language: example_snapshot(EXAMPLE_IDS[language], read_json(report_path))
            for language, report_path in EXAMPLE_REPORTS.items()
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
