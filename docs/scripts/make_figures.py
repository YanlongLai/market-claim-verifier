#!/usr/bin/env python3
"""Build the repository's evidence-backed visuals and keep README in sync.

The builder is deliberately offline. It reads BUILD_LOG.md, committed JSON
traces, evaluation summaries, Mermaid source files, and recorded prompts. It
does not call a model, the SEC, or any other network service.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Keep Matplotlib's generated cache outside the repository when the caller's
# home directory is read-only (as in the managed build environment).
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "market-claim-verifier-matplotlib"),
)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[2]
BUILD_LOG = ROOT / "BUILD_LOG.md"
README = ROOT / "README.md"
VISUALS_DOC = ROOT / "docs" / "VISUALS.md"
REGISTRY = ROOT / "docs" / "figures" / "figures.json"
LIVE_EVIDENCE = ROOT / "docs" / "evidence" / "2026-10-27"
FIGURES = ROOT / "docs" / "figures"
DIAGRAMS = ROOT / "docs" / "diagrams"
PROMPTS = ROOT / "docs" / "prompts"

INK = "#28323c"
MUTED = "#647180"
GRID = "#d7dee5"
PAPER = "#ffffff"
SUPPORTED = "#2f855a"
CONTRADICTED = "#d45d5d"
INSUFFICIENT = "#9aa4ad"
NEUTRAL = "#e8edf2"
META_FILL = "#dce8f0"
BASETEN_FILL = "#d8e0ea"
ACCENT = "#466a83"

STATUS_COLORS = {
    "supported": SUPPORTED,
    "contradicted": CONTRADICTED,
    "insufficient_evidence": INSUFFICIENT,
}

CARD_TRACES = (
    "20261027T221321Z-79b60e38.json",
    "20261027T231724Z-07dbb1c6.json",
)

# The first trace in the post-fix set is the first row of the after-fixes
# verification block in BUILD_LOG.md. The filename is a UTC trace timestamp.
POST_FIX_CUTOFF = "20261027T221321Z"

DIAGRAM_SPECS = (
    ("how-a-claim-is-checked", "What it does"),
    ("real-run-sequence", "Real results"),
    ("providers", "How Meta models are used"),
    ("model-vs-program", "Why you can trust a verdict"),
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected an object in {path}")
    return value


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _sum_numbers(values: Iterable[Any]) -> float | None:
    numbers = [_number(value) for value in values]
    usable = [value for value in numbers if value is not None]
    return sum(usable) if usable else None


def _trace_cost(trace: dict[str, Any]) -> float | None:
    for key in ("cost_usd", "cost"):
        value = _number(trace.get(key))
        if value is not None:
            return value
    requests = trace.get("requests", [])
    return _sum_numbers(item.get("cost") for item in requests if isinstance(item, dict))


def _trace_latency_ms(trace: dict[str, Any]) -> float | None:
    value = _number(trace.get("latency_ms"))
    if value is not None:
        return value
    requests = trace.get("requests", [])
    return _sum_numbers(item.get("latency_ms") for item in requests if isinstance(item, dict))


def _provider(trace: dict[str, Any]) -> str:
    return str(trace.get("provider") or "meta").lower()


def _final_verdict(trace: dict[str, Any]) -> dict[str, Any]:
    value = trace.get("final_verdict")
    return value if isinstance(value, dict) else {}


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _accessions(value: Any) -> list[str]:
    found: set[str] = set()
    for node in _walk(value):
        if isinstance(node, dict):
            accn = node.get("accn")
            if isinstance(accn, str) and accn:
                found.add(accn)
    return sorted(found)


def _evidence_results(trace: dict[str, Any]) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}
    calls = trace.get("tool_calls", [])
    for call in calls if isinstance(calls, list) else []:
        if not isinstance(call, dict):
            continue
        result = call.get("result")
        if not isinstance(result, dict):
            continue
        evidence_id = result.get("evidence_id")
        if isinstance(evidence_id, str):
            evidence[evidence_id] = result
    return evidence


def _subclaim_accessions(trace: dict[str, Any], subclaim: dict[str, Any]) -> list[str]:
    evidence = _evidence_results(trace)
    accessions: set[str] = set()
    evidence_ids = subclaim.get("evidence_ids", [])
    for evidence_id in evidence_ids if isinstance(evidence_ids, list) else []:
        result = evidence.get(str(evidence_id))
        if result is not None:
            accessions.update(_accessions(result))
    return sorted(accessions)


def _split_table_row(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def _verdict_from_cell(cell: str) -> str:
    normalized = re.sub(r"[*`]", "", cell).lower()
    if "contradicted" in normalized:
        return "contradicted"
    if "supported" in normalized:
        return "supported"
    if "insufficient" in normalized:
        return "insufficient_evidence"
    raise ValueError(f"could not find a verdict in BUILD_LOG cell: {cell!r}")


def _build_log_rows() -> list[dict[str, str]]:
    lines = BUILD_LOG.read_text(encoding="utf-8").splitlines()
    header = "| Claim | Before fixes | After fixes | Actual (SEC) |"
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == header)
    except StopIteration as exc:
        raise ValueError("live verification table not found in BUILD_LOG.md") from exc

    rows: list[dict[str, str]] = []
    for line in lines[start + 2 :]:
        if not line.lstrip().startswith("|"):
            break
        parts = _split_table_row(line)
        if len(parts) != 4 or set(parts) <= {"-", "--", "---"}:
            continue
        rows.append(
            {
                "claim": parts[0],
                "before": _verdict_from_cell(parts[1]),
                "after": _verdict_from_cell(parts[2]),
                "actual": parts[3],
            }
        )
    if not rows:
        raise ValueError("live verification table in BUILD_LOG.md has no rows")
    return rows


def _run_date(text: str) -> str:
    match = re.search(r"20\d{2}-\d{2}-\d{2}", text)
    return match.group(0) if match else datetime.now(timezone.utc).date().isoformat()


def _build_log_date() -> str:
    return _run_date(BUILD_LOG.read_text(encoding="utf-8"))


def _source_line(fig: plt.Figure, text: str) -> None:
    fig.text(0.5, 0.012, text, ha="center", va="bottom", color=MUTED, fontsize=8)


def _mpl_safe(value: Any) -> str:
    """Keep literal dollar signs literal in Matplotlib text."""

    return str(value).replace("$", r"\$")


def _style_axis(axis: plt.Axes) -> None:
    axis.set_facecolor(PAPER)
    axis.tick_params(colors=INK, labelsize=9)
    for spine in axis.spines.values():
        spine.set_color(GRID)
    axis.grid(axis="y", color=GRID, linewidth=0.8, alpha=0.75)
    axis.set_axisbelow(True)


def _save(fig: plt.Figure, stem: str) -> list[Path]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    svg = FIGURES / f"{stem}.svg"
    png = FIGURES / f"{stem}.png"
    fig.savefig(svg, format="svg", facecolor=PAPER, bbox_inches="tight")
    fig.savefig(png, format="png", dpi=180, facecolor=PAPER, bbox_inches="tight")
    plt.close(fig)
    return [svg, png]


def make_before_after() -> list[Path]:
    rows = _build_log_rows()
    fig, axis = plt.subplots(figsize=(12.6, 6.2))
    fig.patch.set_facecolor(PAPER)
    axis.set_xlim(0, 1.04)
    axis.set_ylim(-1.05, len(rows) + 0.8)
    axis.axis("off")
    axis.text(0.02, len(rows) + 0.42, "Before vs after the Day 2 fixes", color=INK, fontsize=15, fontweight="bold")
    axis.text(0.02, len(rows) + 0.12, f"Each row is one of the {len(rows)} live claims in BUILD_LOG.md", color=MUTED, fontsize=9)
    axis.text(0.665, len(rows) + 0.18, "Before fixes", color=INK, fontsize=10, fontweight="bold", ha="center")
    axis.text(0.875, len(rows) + 0.18, "After fixes", color=INK, fontsize=10, fontweight="bold", ha="center")

    for index, row in enumerate(rows):
        y = len(rows) - 1 - index
        axis.text(0.02, y, textwrap.fill(_mpl_safe(row["claim"]), 64), color=INK, fontsize=9, va="center")
        if "Alphabet Q3 2025" in row["claim"]:
            axis.text(
                0.02,
                y - 0.28,
                "before: 'first time' was silently ignored",
                color=MUTED,
                fontsize=7.5,
                fontstyle="italic",
                va="center",
            )
        for x, phase in ((0.575, "before"), (0.785, "after")):
            status = row[phase]
            width = 0.17
            axis.add_patch(
                FancyBboxPatch(
                    (x, y - 0.28),
                    width,
                    0.56,
                    boxstyle="round,pad=0.012,rounding_size=0.03",
                    facecolor=STATUS_COLORS[status],
                    edgecolor=STATUS_COLORS[status],
                    alpha=0.92,
                )
            )
            axis.text(
                x + width / 2,
                y,
                status.replace("_", " "),
                color=PAPER,
                fontsize=8.3,
                fontweight="bold",
                ha="center",
                va="center",
            )

    legend_handles = [
        Rectangle((0, 0), 1, 1, facecolor=STATUS_COLORS[status], edgecolor=STATUS_COLORS[status], label=status.replace("_", " "))
        for status in ("supported", "contradicted", "insufficient_evidence")
    ]
    axis.legend(handles=legend_handles, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.77, -0.13))
    fig.tight_layout(rect=(0, 0.05, 1, 0.96))
    _source_line(fig, "Source: BUILD_LOG.md live verification table; traces in docs/evidence/2026-10-27/")
    return _save(fig, "before-after")


def _human_currency(value: float | None) -> str:
    if value is None:
        return "—"
    absolute = abs(value)
    sign = "-" if value < 0 else ""
    if absolute >= 1_000_000_000:
        return f"{sign}${absolute / 1_000_000_000:.3f}B"
    if absolute >= 1_000_000:
        return f"{sign}${absolute / 1_000_000:.3f}M"
    if absolute >= 1_000:
        return f"{sign}${absolute / 1_000:.3f}K"
    return f"{value:g}"


def _actual_label(subclaim: dict[str, Any]) -> str:
    value = _number(subclaim.get("actual_value"))
    claim_type = str(subclaim.get("claim_type") or "")
    if value is None:
        return "—"
    if claim_type == "change_pct":
        return f"{value:+.1f}%"
    if claim_type == "change_abs":
        return _human_currency(value)
    if claim_type in {"record_high", "record_low", "first_time_above"}:
        return "true" if value else "false"
    return _human_currency(value)


def _trace_card_height(trace: dict[str, Any]) -> float:
    subclaims = _final_verdict(trace).get("sub_claims", [])
    count = len(subclaims) if isinstance(subclaims, list) else 0
    return 0.92 + 0.32 * max(1, count)


def _trace_card(axis: plt.Axes, trace: dict[str, Any], trace_name: str, height: float) -> None:
    axis.set_xlim(0, 1)
    axis.set_ylim(0, height)
    axis.axis("off")
    verdict = str(_final_verdict(trace).get("verdict") or "insufficient_evidence")
    status_color = STATUS_COLORS.get(verdict, INSUFFICIENT)
    axis.add_patch(
        FancyBboxPatch(
            (0.005, 0.02),
            0.99,
            height - 0.04,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            facecolor=PAPER,
            edgecolor=GRID,
            linewidth=1.2,
        )
    )
    provider = _provider(trace)
    model = str(trace.get("model") or "")
    cost = _trace_cost(trace)
    latency_ms = _trace_latency_ms(trace)
    cost_text = f"${cost:.4f}" if cost is not None else "—"
    latency_text = f"{latency_ms / 1000:.1f} s" if latency_ms is not None else "—"
    axis.text(0.035, height - 0.15, f"{provider.title()} · {model}", color=INK, fontsize=10, fontweight="bold")
    axis.text(
        0.965,
        height - 0.15,
        verdict.replace("_", " ").upper(),
        color=status_color,
        fontsize=10,
        fontweight="bold",
        ha="right",
    )
    axis.text(0.035, height - 0.36, textwrap.fill(_mpl_safe(trace.get("claim") or ""), 112), color=INK, fontsize=10)
    axis.text(0.965, height - 0.36, f"Cost {cost_text}  ·  Latency {latency_text}", color=MUTED, fontsize=9, ha="right")
    axis.text(0.035, height - 0.58, "SUB-CLAIMS", color=MUTED, fontsize=8, fontweight="bold")

    subclaims = _final_verdict(trace).get("sub_claims", [])
    if not isinstance(subclaims, list):
        subclaims = []
    row_height = 0.30
    for index, subclaim in enumerate(subclaims):
        if not isinstance(subclaim, dict):
            continue
        row_top = height - 0.69 - index * row_height
        row_verdict = str(subclaim.get("program_verdict") or subclaim.get("verdict") or "insufficient_evidence")
        row_color = STATUS_COLORS.get(row_verdict, INSUFFICIENT)
        axis.add_patch(
            Rectangle(
                (0.025, row_top - row_height + 0.02),
                0.95,
                row_height - 0.03,
                facecolor=row_color,
                edgecolor=row_color,
                alpha=0.10,
                linewidth=1,
            )
        )
        subclaim_text = textwrap.fill(_mpl_safe(f"{index + 1}. {subclaim.get('text') or ''}"), 58)
        stated = _mpl_safe(subclaim.get("stated_text") or "—")
        actual = _mpl_safe(_actual_label(subclaim))
        accession = ", ".join(_subclaim_accessions(trace, subclaim)) or "—"
        axis.text(0.045, row_top - 0.035, subclaim_text, color=INK, fontsize=8.2, va="top")
        axis.text(0.50, row_top - 0.035, f"Stated: {stated}\nSEC actual: {actual}", color=INK, fontsize=8.2, va="top")
        axis.text(
            0.745,
            row_top - 0.035,
            f"Program: {row_verdict.replace('_', ' ')}\nAccession: {textwrap.fill(accession, 34)}",
            color=row_color,
            fontsize=8.2,
            va="top",
        )

    axis.text(0.035, 0.075, f"Trace: docs/evidence/2026-10-27/{trace_name}", color=MUTED, fontsize=7.5)


def make_verdict_cards() -> list[Path]:
    traces = []
    for name in CARD_TRACES:
        path = LIVE_EVIDENCE / name
        if not path.is_file():
            raise FileNotFoundError(path)
        traces.append((name, _json(path)))

    heights = [_trace_card_height(trace) for _, trace in traces]
    gap_units = 0.16
    top = 0.885
    bottom = 0.075
    scale = (top - bottom) / (sum(heights) + gap_units * (len(heights) - 1))
    fig = plt.figure(figsize=(13.5, 7.3), facecolor=PAPER)
    fig.text(0.04, 0.965, "Two real runs, checked against SEC evidence", color=INK, fontsize=16, fontweight="bold")
    fig.text(0.04, 0.935, "The model proposes the evidence-backed story; the program computes the displayed verdict.", color=MUTED, fontsize=9.5)
    current_top = top
    for height, (name, trace) in zip(heights, traces):
        axes_height = height * scale
        current_bottom = current_top - axes_height
        axis = fig.add_axes((0.035, current_bottom, 0.93, axes_height))
        _trace_card(axis, trace, name, height)
        current_top = current_bottom - gap_units * scale
    _source_line(fig, "Source: SEC EDGAR XBRL via docs/evidence/2026-10-27/20261027T221321Z-79b60e38.json and 20261027T231724Z-07dbb1c6.json")
    return _save(fig, "verdict-cards")


def make_live_cost_latency() -> list[Path]:
    rows: list[dict[str, Any]] = []
    for path in sorted(LIVE_EVIDENCE.glob("*.json")):
        trace = _json(path)
        cost = _trace_cost(trace)
        latency_ms = _trace_latency_ms(trace)
        if cost is None or latency_ms is None:
            continue
        rows.append(
            {
                "path": path,
                "provider": _provider(trace),
                "cost": cost,
                "latency_s": latency_ms / 1000,
                "verdict": str(_final_verdict(trace).get("verdict") or "insufficient_evidence"),
                "post_fix": path.name >= POST_FIX_CUTOFF,
            }
        )
    if not rows:
        raise ValueError("no live traces with cost and latency")

    fig, axis = plt.subplots(figsize=(11.2, 6.6))
    fig.patch.set_facecolor(PAPER)
    _style_axis(axis)
    provider_style = {
        "meta": ("o", META_FILL, "Meta"),
        "baseten": ("s", BASETEN_FILL, "Baseten"),
    }
    for provider, (marker, fill, _) in provider_style.items():
        for post_fix in (False, True):
            selected = [row for row in rows if row["provider"] == provider and row["post_fix"] is post_fix]
            if not selected:
                continue
            axis.scatter(
                [row["latency_s"] for row in selected],
                [row["cost"] for row in selected],
                marker=marker,
                s=78,
                facecolor=fill if post_fix else PAPER,
                edgecolor=[STATUS_COLORS.get(row["verdict"], INSUFFICIENT) for row in selected],
                linewidth=1.8,
                zorder=3,
            )

    axis.set_title("Development runs, Day 1–2 (not an evaluation)", loc="left", color=INK, fontsize=15, fontweight="bold")
    axis.set_xlabel("Total latency (seconds)", color=INK)
    axis.set_ylabel("Run cost (USD)", color=INK)
    axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:.3f}"))
    provider_handles = [
        Line2D([0], [0], marker=style[0], color="none", markerfacecolor=style[1], markeredgecolor=ACCENT, markersize=8, label=style[2])
        for style in provider_style.values()
    ]
    phase_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=PAPER, markeredgecolor=ACCENT, markersize=8, label="Before Day 2 fixes"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=META_FILL, markeredgecolor=ACCENT, markersize=8, label="After Day 2 fixes"),
    ]
    verdict_handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=PAPER, markeredgecolor=STATUS_COLORS[status], markersize=8, label=status.replace("_", " "))
        for status in ("supported", "contradicted", "insufficient_evidence")
    ]
    first_legend = axis.legend(handles=provider_handles, title="Provider · shape", frameon=False, loc="upper left")
    axis.add_artist(first_legend)
    second_legend = axis.legend(handles=phase_handles, title="Fix phase · fill", frameon=False, loc="lower right")
    axis.add_artist(second_legend)
    axis.legend(handles=verdict_handles, title="Program verdict · outline", frameon=False, loc="upper right")
    fig.text(0.02, 0.94, "Hollow = before fixes · filled = after fixes · outline color = program verdict", color=MUTED, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.06, 1, 0.93))
    _source_line(fig, "Source: SEC EDGAR XBRL-backed traces in docs/evidence/2026-10-27/")
    return _save(fig, "live-cost-latency")


def _valid_eval_summary(path: Path, summary: dict[str, Any]) -> bool:
    required_systems = {
        "single_shot@meta",
        "agent@meta",
        "single_shot@baseten",
        "agent@baseten",
    }
    manifest = summary.get("manifest")
    totals = summary.get("system_totals")
    if not isinstance(manifest, dict) or manifest.get("status") not in {"completed", "complete"}:
        return False
    if not isinstance(totals, dict) or not required_systems.issubset(totals):
        return False
    for system in required_systems:
        total = totals.get(system)
        if not isinstance(total, dict):
            return False
        if _number(total.get("accuracy")) is None or _number(total.get("false_supported_rate")) is None:
            return False
        cost = total.get("cost_usd")
        latency = total.get("latency_ms")
        if not isinstance(cost, dict) or _number(cost.get("total")) is None:
            return False
        if not isinstance(latency, dict) or _number(latency.get("mean")) is None:
            return False
    return path.is_file()


def _complete_eval_summary(eval_dir: Path | None = None) -> tuple[Path, dict[str, Any]] | None:
    if eval_dir is not None:
        candidate = eval_dir / "summary.json" if eval_dir.is_dir() else eval_dir
        try:
            summary = _json(candidate)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"could not read evaluation summary: {candidate}") from exc
        if not _valid_eval_summary(candidate, summary):
            raise ValueError(f"evaluation is not complete or lacks required totals: {candidate}")
        return candidate, summary

    candidates: list[tuple[str, Path, dict[str, Any]]] = []
    for path in ROOT.glob("docs/evidence/eval-*/summary.json"):
        try:
            summary = _json(path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        if not _valid_eval_summary(path, summary):
            continue
        manifest = summary.get("manifest", {})
        started_at = manifest.get("started_at") if isinstance(manifest, dict) else None
        candidates.append((str(started_at or path.parent.name), path, summary))
    if not candidates:
        return None
    _, path, summary = max(candidates, key=lambda item: item[0])
    return path, summary


def _eval_context(path: Path, summary: dict[str, Any]) -> dict[str, Any]:
    manifest = summary.get("manifest") if isinstance(summary.get("manifest"), dict) else {}
    claim_count = manifest.get("claim_count") or manifest.get("n_claims") or summary.get("claim_count")
    split = manifest.get("split") or ", ".join(manifest.get("splits", [])) or "selected"
    run_date = _run_date(str(manifest.get("started_at") or summary.get("generated_at") or path.parent.name))
    return {
        "path": path,
        "summary": summary,
        "manifest": manifest,
        "claim_count": int(claim_count) if _number(claim_count) is not None else "—",
        "split": str(split),
        "run_date": run_date,
    }


def make_eval_summary(path: Path, summary: dict[str, Any]) -> list[Path]:
    context = _eval_context(path, summary)
    systems = ("single_shot@meta", "agent@meta", "single_shot@baseten", "agent@baseten")
    labels = ("Single-shot · Meta", "Agent · Meta", "Single-shot · Baseten", "Agent · Baseten")
    totals = summary["system_totals"]
    metrics = {
        "Accuracy": [float(totals[system]["accuracy"]) for system in systems],
        "False-supported rate": [float(totals[system]["false_supported_rate"]) for system in systems],
        "Total cost (USD)": [float(totals[system]["cost_usd"]["total"]) for system in systems],
        "Mean latency (seconds)": [float(totals[system]["latency_ms"]["mean"]) / 1000 for system in systems],
    }
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 7.6), facecolor=PAPER)
    for axis, (title, values) in zip(axes.flat, metrics.items()):
        _style_axis(axis)
        color = SUPPORTED if title == "Accuracy" else CONTRADICTED if "False" in title else ACCENT
        bars = axis.bar(range(len(labels)), values, color=color, alpha=0.88)
        axis.set_title(title, loc="left", color=INK, fontsize=11, fontweight="bold")
        axis.set_xticks(range(len(labels)), labels, rotation=25, ha="right", fontsize=8)
        if "rate" in title.lower() or title == "Accuracy":
            axis.set_ylim(0, 1)
            axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0%}"))
        elif "cost" in title.lower():
            axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:.2f}"))
        else:
            axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
        for bar, value in zip(bars, values):
            label = (
                f"{value:.0%}"
                if "rate" in title.lower() or title == "Accuracy"
                else f"${value:.2f}"
                if "cost" in title.lower()
                else f"{value:.1f}s"
            )
            axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), label, ha="center", va="bottom", fontsize=8, color=INK)
    fig.suptitle("Evaluation summary", x=0.05, ha="left", color=INK, fontsize=16, fontweight="bold")
    fig.text(0.05, 0.925, f"n = {context['claim_count']} {context['split']} claims · run {context['run_date']}", color=MUTED, fontsize=9.5)
    fig.tight_layout(rect=(0, 0.08, 1, 0.90))
    _source_line(fig, f"Source: {path.relative_to(ROOT)}")
    return _save(fig, "eval-summary")


def make_data_quality(path: Path | None = None) -> list[Path]:
    """Render cached-companyfacts checks passed versus anomalies per issuer."""

    source = path or (ROOT / "docs" / "evidence" / "data-quality-2026-10-27.json")
    report = _json(source)
    issuers = report.get("issuers", [])
    if not isinstance(issuers, list):
        raise ValueError(f"data-quality report has no issuer list: {source}")
    rows = [item for item in issuers if isinstance(item, dict)]
    labels = [str(item.get("ticker") or item.get("cik") or "—") for item in rows]
    passed = [float(item.get("checks_passed", 0) or 0) for item in rows]
    anomalies = [float(item.get("anomalies", 0) or 0) for item in rows]
    width = max(13.5, min(19.0, 8.0 + len(rows) * 0.34))
    fig, axis = plt.subplots(figsize=(width, 7.3), facecolor=PAPER)
    _style_axis(axis)
    positions = list(range(len(rows)))
    bar_width = 0.38
    first = axis.bar(
        [position - bar_width / 2 for position in positions],
        passed,
        width=bar_width,
        color=SUPPORTED,
        alpha=0.9,
        label="Checks passed",
    )
    second = axis.bar(
        [position + bar_width / 2 for position in positions],
        anomalies,
        width=bar_width,
        color=CONTRADICTED,
        alpha=0.9,
        label="Anomalies",
    )
    axis.set_title(
        "Cached SEC data quality by issuer",
        loc="left",
        color=INK,
        fontsize=15,
        fontweight="bold",
        pad=24,
    )
    axis.text(
        0,
        1.01,
        f"Snapshot {report.get('snapshot_date', '—')} · {len(rows)} issuers · flow metrics only",
        transform=axis.transAxes,
        color=MUTED,
        fontsize=9.5,
        va="bottom",
    )
    axis.set_xticks(positions, labels, rotation=60, ha="right", fontsize=8)
    axis.set_ylabel("Count", color=MUTED, fontsize=9)
    axis.legend(frameon=False, loc="upper right")
    for bars in (first, second):
        for bar in bars:
            height = bar.get_height()
            if height:
                axis.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{height:g}",
                    ha="center",
                    va="bottom",
                    fontsize=7.5,
                    color=INK,
                )
    fig.tight_layout(rect=(0, 0.08, 1, 0.87))
    _source_line(fig, f"Source: {_relative(source)}")
    return _save(fig, "data-quality")


def _relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _expand_sources(patterns: Iterable[str]) -> list[Path]:
    found: dict[str, Path] = {}
    for pattern in patterns:
        candidate = Path(pattern)
        if candidate.is_absolute():
            if candidate.is_file():
                matches = [candidate]
            elif candidate.is_dir():
                matches = list(candidate.glob("**/*"))
            else:
                matches = []
        else:
            matches = list(ROOT.glob(pattern))
        for path in matches:
            if path.is_file():
                found[_relative(path)] = path
    return [found[key] for key in sorted(found)]


def _inputs_sha256(patterns: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for path in _expand_sources(patterns):
        digest.update(_relative(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_registry() -> dict[str, Any]:
    if not REGISTRY.is_file():
        return {"version": 1, "figures": []}
    value = _json(REGISTRY)
    figures = value.get("figures")
    if not isinstance(figures, list):
        raise ValueError(f"registry has no figures list: {REGISTRY}")
    return value


def _write_registry(entries: list[dict[str, Any]]) -> None:
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps({"version": 1, "figures": entries}, indent=2) + "\n", encoding="utf-8")


def _entry(
    figure_id: str,
    outputs: list[str],
    kind: str,
    generator: str,
    data_sources: list[str],
    readme_section: str,
    *,
    generated_at: str,
) -> dict[str, Any]:
    return {
        "id": figure_id,
        "output": outputs,
        "kind": kind,
        "generator": generator,
        "data_sources": data_sources,
        "readme_section": readme_section,
        "generated_at": generated_at,
        "inputs_sha256": _inputs_sha256(data_sources),
    }


def _prior_by_id(prior: dict[str, Any]) -> dict[str, dict[str, Any]]:
    value = {}
    for entry in prior.get("figures", []):
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            value[entry["id"]] = entry
    return value


def _registry_entries(evaluation: dict[str, Any] | None, prior: dict[str, Any]) -> list[dict[str, Any]]:
    previous = _prior_by_id(prior)
    generated_at = _now()
    entries: list[dict[str, Any]] = []

    hero_source = ["docs/prompts/hero-image.md"]
    hero_previous = previous.get("hero", {})
    hero_output = FIGURES / "hero.png"
    hero_generated_at = str(hero_previous.get("generated_at") or _file_timestamp(hero_output) or generated_at)
    hero_entry = _entry(
        "hero",
        ["docs/figures/hero.png"],
        "ai_image",
        "docs/prompts/hero-image.md",
        hero_source,
        "Overview",
        generated_at=hero_generated_at,
    )
    if hero_previous.get("inputs_sha256"):
        # --all is intentionally no-model-call, so an edited prompt must stay
        # stale until a human regenerates the image with the recorded prompt.
        hero_entry["inputs_sha256"] = hero_previous["inputs_sha256"]
    entries.append(hero_entry)

    entries.append(
        _entry(
            "before-after",
            ["docs/figures/before-after.svg", "docs/figures/before-after.png", "README.md"],
            "chart",
            "make_before_after",
            ["BUILD_LOG.md"],
            "Real results",
            generated_at=generated_at,
        )
    )
    entries.append(
        _entry(
            "verdict-cards",
            ["docs/figures/verdict-cards.svg", "docs/figures/verdict-cards.png", "README.md"],
            "card",
            "make_verdict_cards",
            [f"docs/evidence/2026-10-27/{name}" for name in CARD_TRACES],
            "What it does",
            generated_at=generated_at,
        )
    )
    if evaluation is not None:
        eval_path = Path(evaluation["path"])
        eval_dir = eval_path.parent
        eval_source = [_relative(eval_dir / "*.json")]
        entries.append(
            _entry(
                "eval-summary",
                ["docs/figures/eval-summary.svg", "docs/figures/eval-summary.png", "README.md"],
                "chart",
                "make_eval_summary",
                eval_source,
                "Real results",
                generated_at=generated_at,
            )
        )
    data_quality_source = ROOT / "docs" / "evidence" / "data-quality-2026-10-27.json"
    if data_quality_source.is_file():
        entries.append(
            _entry(
                "data-quality",
                ["docs/figures/data-quality.svg", "docs/figures/data-quality.png"],
                "chart",
                "make_data_quality",
                ["docs/evidence/data-quality-2026-10-27.json"],
                "Data quality",
                generated_at=generated_at,
            )
        )
    entries.append(
        _entry(
            "live-cost-latency",
            ["docs/figures/live-cost-latency.svg", "docs/figures/live-cost-latency.png", "README.md", "docs/VISUALS.md"],
            "chart",
            "make_live_cost_latency",
            ["BUILD_LOG.md", "docs/evidence/2026-10-27/*.json"],
            "Real results / Visuals index",
            generated_at=generated_at,
        )
    )

    for diagram_id, readme_section in DIAGRAM_SPECS:
        entries.append(
            _entry(
                diagram_id,
                ["README.md"],
                "diagram",
                f"docs/diagrams/{diagram_id}.mmd",
                [f"docs/diagrams/{diagram_id}.mmd"],
                readme_section,
                generated_at=generated_at,
            )
        )
    return entries


def _file_timestamp(path: Path) -> str | None:
    if not path.is_file():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _diagram_block(diagram_id: str) -> str:
    source = (DIAGRAMS / f"{diagram_id}.mmd").read_text(encoding="utf-8").strip()
    return f"```mermaid\n{source}\n```"


def _marker_bounds(kind: str, marker_id: str) -> tuple[str, str]:
    return f"<!-- {kind}:{marker_id}:start -->", f"<!-- {kind}:{marker_id}:end -->"


def _replace_marker(text: str, kind: str, marker_id: str, body: str, *, strict: bool = True) -> str:
    start, end = _marker_bounds(kind, marker_id)
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{body.strip()}\n{end}"
    if not pattern.search(text):
        if strict:
            raise ValueError(f"missing {kind} marker for {marker_id}")
        return text
    return pattern.sub(replacement, text, count=1)


def _figure_body(figure_id: str, evaluation: dict[str, Any] | None) -> str:
    date = _build_log_date()
    if figure_id == "hero":
        return (
            "![Editorial illustration of a sentence connected to filing sheets](docs/figures/hero.png)\n\n"
            "*AI-generated illustration: a sentence being checked against filings.* "
            "The reusable prompt is recorded in [`docs/prompts/hero-image.md`](docs/prompts/hero-image.md)."
        )
    if figure_id == "verdict-cards":
        return (
            "![Two real runs rendered as evidence-backed verdict cards](docs/figures/verdict-cards.svg)\n\n"
            f"*Two real traces, run {date}; each card shows the program verdict and cited SEC evidence.*"
        )
    if figure_id == "before-after":
        rows = _build_log_rows()
        return (
            "![Before and after Day 2 fixes](docs/figures/before-after.svg)\n\n"
            f"*Before/after chart: n = {len(rows)} live claims from BUILD_LOG.md, run {date}."
            "*"
        )
    if figure_id == "live-cost-latency":
        count = sum(
            1
            for path in LIVE_EVIDENCE.glob("*.json")
            if _trace_cost(_json(path)) is not None and _trace_latency_ms(_json(path)) is not None
        )
        if evaluation is None:
            return (
                "![Development-run cost and latency](docs/figures/live-cost-latency.svg)\n\n"
                f"*Development runs, Day 1–2: n = {count} traces; not an evaluation.*"
            )
        return "Development-run cost and latency is documented in [`docs/VISUALS.md`](docs/VISUALS.md); the evaluation figure above is the results view."
    if figure_id == "eval-summary":
        if evaluation is None:
            return ""
        return (
            "![Evaluation cost, latency, accuracy, and false-supported rate](docs/figures/eval-summary.svg)\n\n"
            f"*Evaluation: n = {evaluation['claim_count']} {evaluation['split']} claims, run {evaluation['run_date']}."
            "*"
        )
    raise KeyError(figure_id)


def _sync_readme(evaluation: dict[str, Any] | None) -> None:
    text = README.read_text(encoding="utf-8")
    for diagram_id, _ in DIAGRAM_SPECS:
        text = _replace_marker(text, "diagram", diagram_id, _diagram_block(diagram_id))
    for figure_id in ("hero", "verdict-cards", "before-after", "eval-summary", "live-cost-latency"):
        text = _replace_marker(text, "figure", figure_id, _figure_body(figure_id, evaluation))
    README.write_text(text, encoding="utf-8")


def _output_label(output: str) -> str:
    if output == "README.md":
        return "`README.md`"
    if output == "docs/VISUALS.md":
        return "`docs/VISUALS.md`"
    target = output.removeprefix("docs/") if output.startswith("docs/") else output
    return f"[`{output}`]({target})"


def _visuals_registry_table(entries: list[dict[str, Any]]) -> str:
    lines = [
        "| ID | Kind | Output | Generator | Data sources | README section | Inputs SHA-256 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        outputs = "<br>".join(_output_label(str(value)) for value in entry["output"])
        sources = "<br>".join(f"`{value}`" for value in entry["data_sources"])
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{entry['id']}`",
                    str(entry["kind"]),
                    outputs,
                    f"`{entry['generator']}`",
                    sources,
                    str(entry["readme_section"]),
                    f"`{entry['inputs_sha256'][:12]}…`",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _sync_visuals_doc(entries: list[dict[str, Any]]) -> None:
    text = VISUALS_DOC.read_text(encoding="utf-8")
    text = _replace_marker(text, "registry", "figures", _visuals_registry_table(entries))
    live_count = sum(
        1
        for path in LIVE_EVIDENCE.glob("*.json")
        if _trace_cost(_json(path)) is not None and _trace_latency_ms(_json(path)) is not None
    )
    live_body = (
        "![Development-run cost and latency](figures/live-cost-latency.svg)\n\n"
        f"*Development runs, Day 1–2: n = {live_count} traces; hollow markers are pre-fix and filled markers are post-fix.*"
    )
    text = _replace_marker(text, "figure", "live-cost-latency", live_body)
    VISUALS_DOC.write_text(text, encoding="utf-8")


def _body_between(text: str, kind: str, marker_id: str) -> str | None:
    start, end = _marker_bounds(kind, marker_id)
    pattern = re.compile(re.escape(start) + r"\n?(.*?)\n?" + re.escape(end), re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def _check_registry() -> list[str]:
    if not REGISTRY.is_file():
        return [f"registry missing: {_relative(REGISTRY)}"]
    registry = _load_registry()
    entries = [entry for entry in registry.get("figures", []) if isinstance(entry, dict)]
    stale: list[str] = []
    evaluation_raw = _complete_eval_summary()
    evaluation = _eval_context(*evaluation_raw) if evaluation_raw is not None else None
    for entry in entries:
        figure_id = str(entry.get("id") or "(unnamed)")
        sources = entry.get("data_sources")
        if not isinstance(sources, list):
            stale.append(f"{figure_id}: data_sources is missing")
            continue
        current_hash = _inputs_sha256(str(source) for source in sources)
        if current_hash != entry.get("inputs_sha256"):
            stale.append(f"{figure_id}: inputs changed (rerun --all)")
        outputs = entry.get("output", [])
        if isinstance(outputs, list):
            for output in outputs:
                if not (ROOT / str(output)).is_file():
                    stale.append(f"{figure_id}: missing output {output}")
        if entry.get("kind") == "diagram":
            expected = _diagram_block(figure_id)
            actual = _body_between(README.read_text(encoding="utf-8"), "diagram", figure_id)
            if actual != expected:
                stale.append(f"{figure_id}: README is out of sync")

    readme_text = README.read_text(encoding="utf-8")
    expected_by_id = {str(entry.get("id")): entry for entry in entries}
    if evaluation is not None and "eval-summary" not in expected_by_id:
        stale.append("eval-summary: complete evaluation found (rerun --all)")
    for figure_id in ("hero", "verdict-cards", "before-after", "live-cost-latency"):
        if figure_id in expected_by_id and _body_between(readme_text, "figure", figure_id) != _figure_body(figure_id, evaluation):
            stale.append(f"{figure_id}: README caption/embed is out of sync")
    if "eval-summary" in expected_by_id and _body_between(readme_text, "figure", "eval-summary") != _figure_body("eval-summary", evaluation):
        stale.append("eval-summary: README caption/embed is out of sync")

    if VISUALS_DOC.is_file():
        visuals_text = VISUALS_DOC.read_text(encoding="utf-8")
        if _body_between(visuals_text, "registry", "figures") != _visuals_registry_table(entries):
            stale.append("registry: docs/VISUALS.md table is out of sync")
        live_count = sum(
            1
            for path in LIVE_EVIDENCE.glob("*.json")
            if _trace_cost(_json(path)) is not None and _trace_latency_ms(_json(path)) is not None
        )
        live_body = (
            "![Development-run cost and latency](figures/live-cost-latency.svg)\n\n"
            f"*Development runs, Day 1–2: n = {live_count} traces; hollow markers are pre-fix and filled markers are post-fix.*"
        )
        if _body_between(visuals_text, "figure", "live-cost-latency") != live_body:
            stale.append("live-cost-latency: docs/VISUALS.md embed is out of sync")
    return stale


def _run_all(eval_arg: str | None) -> None:
    evaluation_raw = _complete_eval_summary(Path(eval_arg).resolve() if eval_arg else None)
    evaluation = _eval_context(*evaluation_raw) if evaluation_raw is not None else None
    prior = _load_registry()
    generated: list[Path] = []
    generated.extend(make_before_after())
    generated.extend(make_verdict_cards())
    generated.extend(make_live_cost_latency())
    data_quality_source = ROOT / "docs" / "evidence" / "data-quality-2026-10-27.json"
    if data_quality_source.is_file():
        generated.extend(make_data_quality(data_quality_source))
    if evaluation_raw is not None:
        generated.extend(make_eval_summary(*evaluation_raw))
    _sync_readme(evaluation)
    entries = _registry_entries(evaluation, prior)
    _sync_visuals_doc(entries)
    _write_registry(entries)
    for path in generated:
        print(_relative(path))
    print(_relative(REGISTRY))
    print(_relative(VISUALS_DOC))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--all", action="store_true", help="regenerate evidence-backed figures and sync documentation")
    modes.add_argument("--check", action="store_true", help="list figures whose inputs or embeds are stale")
    parser.add_argument("--eval", metavar="DIR", help="choose an evaluation directory containing summary.json")
    args = parser.parse_args(argv)
    try:
        if args.all:
            _run_all(args.eval)
            return 0
        stale = _check_registry()
    except (OSError, ValueError, KeyError) as exc:
        print(f"figure check failed: {exc}")
        return 1
    if stale:
        print("stale figures:")
        for item in stale:
            print(f"- {item}")
        return 1
    print("figures are up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
