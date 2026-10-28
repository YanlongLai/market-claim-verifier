"""Offline data-quality checks for the cached SEC companyfacts snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .edgar import (
    ADDITIVE_METRICS,
    METRIC_ALIASES,
    METRIC_UNITS,
    STATEMENT_FORMS,
)
from .fiscal import normalize_fiscal_labels


DEFAULT_SNAPSHOT_DATE = "2026-10-27"
# Year-to-date totals can only fall for metrics that can be negative in a quarter (income lines), so monotonicity is
# checked only where a decrease is a genuine inconsistency.
CUMULATIVE_NON_DECREASING = {"revenue", "gross_profit", "capex", "rd_expense"}
# Later filings routinely revise earlier periods (reclassifications, discontinued operations). Revisions above this
# relative size are reported as material; smaller ones as minor.
MATERIAL_REVISION = 0.005
DEFAULT_CACHE_DIR = Path(".cache")
DEFAULT_REPORT_PATH = Path("docs/evidence/data-quality-2026-10-27.json")
DEFAULT_DOC_PATH = Path("docs/DATA_QUALITY.md")
FLOW_METRICS = tuple(metric for metric in METRIC_ALIASES if metric in ADDITIVE_METRICS)
MAX_EXAMPLES = 12


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _date(value: Any) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _days(start: Any, end: Any) -> int | None:
    start_date = _date(start)
    end_date = _date(end)
    if start_date is None or end_date is None:
        return None
    return (end_date - start_date).days + 1


def _period_type(fact: Mapping[str, Any]) -> str:
    start = _date(fact.get("start"))
    end = _date(fact.get("end"))
    if start is None or end is None:
        return "instant"
    duration = (end - start).days + 1
    if 80 <= duration <= 100:
        return "quarter"
    if 300 <= duration <= 380:
        return "annual"
    return "ytd"


def _fiscal_year(fact: Mapping[str, Any]) -> int | None:
    try:
        value = int(fact.get("fy"))
    except (TypeError, ValueError):
        end = _date(fact.get("end"))
        return end.year if end is not None else None
    return value if 1900 <= value <= 2200 else None


def _form(fact: Mapping[str, Any]) -> str:
    return str(fact.get("form") or "").strip().upper()


def _statement(fact: Mapping[str, Any]) -> bool:
    return _form(fact) in STATEMENT_FORMS


def _filed(fact: Mapping[str, Any]) -> str:
    return str(fact.get("filed") or "").strip()


def _accn(fact: Mapping[str, Any]) -> str:
    return str(fact.get("accn") or "").strip()


def _fact_sort_key(item: tuple[int, str, Mapping[str, Any]]) -> tuple[Any, ...]:
    concept_index, _unit, fact = item
    return (
        1 if _statement(fact) else 0,
        # METRIC_ALIASES is ordered from the current concept to older
        # fallbacks; ``max`` therefore needs the inverse index.
        -concept_index,
        _filed(fact),
        _accn(fact),
    )


def _metric_facts(
    document: Mapping[str, Any], metric: str
) -> list[tuple[int, str, Mapping[str, Any]]]:
    facts = document.get("facts", {})
    result: list[tuple[int, str, Mapping[str, Any]]] = []
    for concept_index, (namespace, concept) in enumerate(METRIC_ALIASES[metric]):
        namespace_data = facts.get(namespace, {}) if isinstance(facts, Mapping) else {}
        concept_data = namespace_data.get(concept) if isinstance(namespace_data, Mapping) else None
        if not isinstance(concept_data, Mapping):
            continue
        units = concept_data.get("units")
        if not isinstance(units, Mapping):
            continue
        preferred_units = METRIC_UNITS.get(metric, ())
        unit_items = sorted(
            units.items(), key=lambda item: (0 if item[0] in preferred_units else 1, str(item[0]))
        )
        for unit, values in unit_items:
            if preferred_units and str(unit) not in preferred_units:
                continue
            if not isinstance(values, list):
                continue
            result.extend(
                (concept_index, str(unit), {**fact, "_concept": concept})
                for fact in values
                if isinstance(fact, Mapping) and _date(fact.get("end")) is not None
            )
    return result


def _select_period(
    entries: Iterable[tuple[int, str, Mapping[str, Any]]],
) -> tuple[int, str, Mapping[str, Any]] | None:
    values = list(entries)
    if not values:
        return None
    statement_values = [item for item in values if _statement(item[2])]
    eligible = statement_values or values
    # Form quality outranks concept alias; the latest filed row wins within the
    # selected family, matching the production EDGAR selector.
    return max(eligible, key=_fact_sort_key)


def _period_key(fact: Mapping[str, Any]) -> tuple[int, str] | None:
    fiscal_year = _fiscal_year(fact)
    fp = str(fact.get("fp") or "").strip().upper()
    if fiscal_year is None or fp not in {"Q1", "Q2", "Q3", "Q4", "FY"}:
        return None
    return fiscal_year, fp


def _selected_periods(
    entries: list[tuple[int, str, Mapping[str, Any]]],
) -> dict[tuple[int, str], tuple[int, str, Mapping[str, Any]]]:
    grouped: dict[tuple[int, str], list[tuple[int, str, Mapping[str, Any]]]] = defaultdict(list)
    for item in entries:
        key = _period_key(item[2])
        if key is not None:
            grouped[key].append(item)
    selected: dict[tuple[int, str], tuple[int, str, Mapping[str, Any]]] = {}
    for key, values in grouped.items():
        chosen = _select_period(values)
        if chosen is not None:
            selected[key] = chosen
    return selected


def _source_facts(item: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if item is None:
        return []
    return [
        {
            "accn": _accn(item),
            "form": _form(item),
            "filed": _filed(item),
            "start": item.get("start"),
            "end": item.get("end"),
            "value": item.get("val"),
        }
    ]


def _derived_quarters(
    selected: Mapping[tuple[int, str], tuple[int, str, Mapping[str, Any]]],
) -> dict[tuple[int, int], dict[str, Any]]:
    """Return direct or YTD-derived quarters, keyed by fiscal year/quarter."""

    quarters: dict[tuple[int, int], dict[str, Any]] = {}
    for fiscal_year in sorted({year for year, _ in selected}):
        for quarter in range(1, 5):
            direct = selected.get((fiscal_year, f"Q{quarter}"))
            if direct is not None and _period_type(direct[2]) == "quarter":
                value = _number(direct[2].get("val"))
                if value is not None:
                    quarters[(fiscal_year, quarter)] = {
                        "value": value,
                        "derived": False,
                        "period": f"FY{fiscal_year}Q{quarter}",
                        "facts": _source_facts(direct[2]),
                    }
                    continue

            current_key = (fiscal_year, f"Q{quarter}")
            current = selected.get(current_key)
            if current is None:
                if quarter == 4:
                    current = selected.get((fiscal_year, "FY"))
                else:
                    continue
            if current is None:
                continue
            current_value = _number(current[2].get("val"))
            if current_value is None:
                continue

            if quarter == 1:
                # A Q1 YTD value is the quarter itself.
                if _period_type(current[2]) in {"quarter", "ytd"}:
                    quarters[(fiscal_year, quarter)] = {
                        "value": current_value,
                        "derived": _period_type(current[2]) != "quarter",
                        "period": f"FY{fiscal_year}Q1",
                        "facts": _source_facts(current[2]),
                    }
                continue

            previous = selected.get((fiscal_year, f"Q{quarter - 1}"))
            if quarter == 4:
                previous = selected.get((fiscal_year, "Q3"))
            previous_value = _number(previous[2].get("val")) if previous else None
            if previous is None or previous_value is None:
                continue
            if quarter == 4:
                # Annual minus Q3 YTD is the only valid Q4 derivation.
                if _period_type(current[2]) != "annual" or _period_type(previous[2]) != "ytd":
                    continue
            else:
                if _period_type(current[2]) != "ytd":
                    continue
            quarters[(fiscal_year, quarter)] = {
                "value": current_value - previous_value,
                "derived": True,
                "period": f"FY{fiscal_year}Q{quarter}",
                "facts": _source_facts(current[2]) + _source_facts(previous[2]),
            }
    return quarters


def _annual_checks(
    selected: Mapping[tuple[int, str], tuple[int, str, Mapping[str, Any]]],
    quarters: Mapping[tuple[int, int], Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    for fiscal_year in sorted({year for year, fp in selected if fp == "FY"}):
        annual = selected.get((fiscal_year, "FY"))
        annual_value = _number(annual[2].get("val")) if annual else None
        rows = [quarters.get((fiscal_year, quarter)) for quarter in range(1, 5)]
        if annual is None or annual_value is None or any(row is None for row in rows):
            continue
        quarter_sum = sum(float(row["value"]) for row in rows if row is not None)
        delta = quarter_sum - annual_value
        tolerance = max(abs(annual_value) * 0.005, 1_000_000.0)
        passed = abs(delta) <= tolerance
        check = {
            "fiscal_year": fiscal_year,
            "annual_value": annual_value,
            "quarterly_sum": quarter_sum,
            "delta": delta,
            "tolerance": tolerance,
            "passed": passed,
            "annual_accessions": [_accn(annual[2])] if _accn(annual[2]) else [],
            "quarter_accessions": sorted(
                {
                    fact["accn"]
                    for row in rows
                    for fact in row["facts"]
                    if fact.get("accn")
                }
            ),
        }
        checks.append(check)
        if not passed:
            anomalies.append({"type": "annual_sum_mismatch", **check})
    return checks, anomalies


def _ytd_checks(
    selected: Mapping[tuple[int, str], tuple[int, str, Mapping[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    for fiscal_year in sorted({year for year, _ in selected}):
        rows: list[tuple[str, Mapping[str, Any]]] = []
        for fp in ("Q1", "Q2", "Q3", "FY"):
            selected_item = selected.get((fiscal_year, fp))
            if selected_item is None:
                continue
            fact = selected_item[2]
            value = _number(fact.get("val"))
            if value is None:
                continue
            # Q2/Q3 must be cumulative facts; Q1 is cumulative by definition.
            if fp != "Q1" and fp != "FY" and _period_type(fact) != "ytd":
                continue
            rows.append((fp, fact))
        if len(rows) < 2:
            continue
        values = [_number(fact.get("val")) for _fp, fact in rows]
        if any(value is None for value in values):
            continue
        if any(value < 0 for value in values if value is not None):
            continue
        check = {
            "fiscal_year": fiscal_year,
            "periods": [fp for fp, _fact in rows],
            "values": [float(value) for value in values if value is not None],
            "passed": True,
            "accessions": [_accn(fact) for _fp, fact in rows if _accn(fact)],
        }
        for (previous_fp, previous_fact), (current_fp, current_fact) in zip(rows, rows[1:]):
            previous_value = _number(previous_fact.get("val"))
            current_value = _number(current_fact.get("val"))
            if previous_value is None or current_value is None or current_value >= previous_value:
                continue
            check.update(
                {
                    "passed": False,
                    "from_period": previous_fp,
                    "to_period": current_fp,
                    "from_value": previous_value,
                    "to_value": current_value,
                    "from_accn": _accn(previous_fact),
                    "to_accn": _accn(current_fact),
                }
            )
            break
        checks.append(check)
        if not check["passed"]:
            anomalies.append({"type": "ytd_drop", **check})
    return checks, anomalies


def _group_exact_periods(
    entries: Iterable[tuple[int, str, Mapping[str, Any]]],
) -> dict[tuple[int, str, str | None, str | None], list[tuple[int, str, Mapping[str, Any]]]]:
    grouped: dict[tuple[int, str, str | None, str | None], list[tuple[int, str, Mapping[str, Any]]]] = defaultdict(list)
    for item in entries:
        fact = item[2]
        grouped[(item[0], item[1], fact.get("start"), fact.get("end"))].append(item)
    return grouped


def _value_groups(
    facts: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for fact in facts:
        value = fact.get("val")
        group = next((candidate for candidate in groups if candidate["value"] == value), None)
        if group is None:
            group = {"value": value, "accessions": set()}
            groups.append(group)
        accn = _accn(fact)
        if accn:
            group["accessions"].add(accn)
    return [
        {"value": group["value"], "accessions": sorted(group["accessions"])}
        for group in groups
    ]


def _restatement_report(
    entries: Iterable[tuple[int, str, Mapping[str, Any]]],
) -> tuple[int, int, list[dict[str, Any]]]:
    """Return (revised periods, material revisions, examples) for periods reported with different values."""

    examples: list[dict[str, Any]] = []
    count = 0
    material = 0
    for (_concept_index, unit, start, end), values in _group_exact_periods(entries).items():
        value_groups = _value_groups(item[2] for item in values)
        if len(value_groups) <= 1:
            continue
        count += 1
        numbers = [abs(float(group["value"])) for group in value_groups if _number(group["value"]) is not None]
        spread = (max(numbers) - min(numbers)) / max(max(numbers), 1.0) if numbers else 0.0
        is_material = spread > MATERIAL_REVISION
        material += int(is_material)
        if len(examples) >= MAX_EXAMPLES:
            continue
        facts = [item[2] for item in values]
        examples.append(
            {
                "concept": str(facts[0].get("_concept") or "") or None,
                "unit": unit,
                "start": start,
                "end": end,
                "relative_change": round(spread, 6),
                "material": is_material,
                "values_seen": value_groups,
                "accessions": sorted({_accn(fact) for fact in facts if _accn(fact)}),
                "forms": sorted({_form(fact) for fact in facts if _form(fact)}),
            }
        )
    return count, material, examples


def _fallback_report(
    entries: Iterable[tuple[int, str, Mapping[str, Any]]],
) -> tuple[int, list[dict[str, Any]]]:
    grouped = _group_exact_periods(entries)
    examples: list[dict[str, Any]] = []
    count = 0
    for (_concept_index, unit, start, end), values in grouped.items():
        facts = [item[2] for item in values]
        if not facts or any(_statement(fact) for fact in facts):
            continue
        count += 1
        if len(examples) < MAX_EXAMPLES:
            examples.append(
                {
                    "concept": str(facts[0].get("_concept") or "") or None,
                    "unit": unit,
                    "start": start,
                    "end": end,
                    "forms": sorted({_form(fact) for fact in facts if _form(fact)}),
                    "accessions": sorted({_accn(fact) for fact in facts if _accn(fact)}),
                }
            )
    return count, examples


def _metric_quality(document: Mapping[str, Any], metric: str) -> dict[str, Any]:
    entries = _metric_facts(document, metric)
    selected = _selected_periods(entries)
    quarters = _derived_quarters(selected)
    annual_checks, annual_anomalies = _annual_checks(selected, quarters)
    if metric in CUMULATIVE_NON_DECREASING:
        ytd_checks, ytd_anomalies = _ytd_checks(selected)
    else:
        ytd_checks, ytd_anomalies = [], []
    restatement_count, material_count, restatement_examples = _restatement_report(entries)
    fallback_count, fallback_examples = _fallback_report(entries)
    anomalies = [
        *annual_anomalies,
        *ytd_anomalies,
        *[
            {"type": "form_fallback", **example}
            for example in fallback_examples
        ],
    ]
    checks_passed = sum(bool(check.get("passed")) for check in annual_checks)
    checks_total = len(annual_checks)
    checks_passed += sum(bool(check.get("passed")) for check in ytd_checks)
    checks_total += len(ytd_checks)
    if entries:
        checks_total += 2
        checks_passed += int(material_count == 0) + int(fallback_count == 0)
    return {
        "available": bool(entries),
        "checks_passed": checks_passed,
        "checks_total": checks_total,
        "anomalies": anomalies,
        "annual_sum_vs_annual": {
            "eligible": len(annual_checks),
            "passed": sum(bool(check.get("passed")) for check in annual_checks),
            "anomalies": annual_anomalies,
            "checks": annual_checks,
        },
        "ytd_monotonicity": {
            "eligible": len(ytd_checks),
            "passed": sum(bool(check.get("passed")) for check in ytd_checks),
            "anomalies": ytd_anomalies,
            "checks": ytd_checks,
        },
        "restatements": {
            "count": restatement_count,
            "material": material_count,
            "examples": restatement_examples,
        },
        "form_fallback": {
            "count": fallback_count,
            "examples": fallback_examples,
        },
    }


def _ticker_map(path: Path) -> dict[str, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    records = value.get("data", []) if isinstance(value, Mapping) else []
    if not isinstance(records, list) or not records:
        records = list(value.values()) if isinstance(value, Mapping) else []
    result: dict[str, str] = {}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        try:
            cik = f"{int(record.get('cik_str')):010d}"
        except (TypeError, ValueError):
            continue
        ticker = str(record.get("ticker") or "").strip().upper()
        if ticker and cik not in result:
            result[cik] = ticker
    return result


def _issuer_report(
    path: Path, document: Mapping[str, Any], ticker: str,
) -> dict[str, Any]:
    cik = f"{int(document.get('cik') or path.stem.removeprefix('companyfacts-CIK')):010d}"
    metrics = {metric: _metric_quality(document, metric) for metric in FLOW_METRICS}
    return {
        "cik": cik,
        "ticker": ticker,
        "entity": str(document.get("entityName") or ticker or cik),
        "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "metrics": metrics,
        "checks_passed": sum(int(value["checks_passed"]) for value in metrics.values()),
        "checks_total": sum(int(value["checks_total"]) for value in metrics.values()),
        "anomalies": sum(len(value["anomalies"]) for value in metrics.values()),
        "restated_periods": sum(
            int(value["restatements"]["count"]) for value in metrics.values()
        ),
        "material_revisions": sum(
            int(value["restatements"]["material"]) for value in metrics.values()
        ),
        "form_fallback_periods": sum(
            int(value["form_fallback"]["count"]) for value in metrics.values()
        ),
    }


def build_data_quality_report(
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
    *,
    snapshot_date: str = DEFAULT_SNAPSHOT_DATE,
) -> dict[str, Any]:
    """Build a deterministic report from local companyfacts JSON only."""

    cache = Path(cache_dir)
    ticker_by_cik = _ticker_map(cache / "company_tickers.json")
    issuers: list[dict[str, Any]] = []
    sha256: dict[str, str] = {}
    for path in sorted(cache.glob("companyfacts-CIK*.json")):
        if path.name.endswith(".meta.json"):
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(document, dict):
            continue
        normalize_fiscal_labels(document)
        try:
            cik = f"{int(document.get('cik') or path.stem.removeprefix('companyfacts-CIK')):010d}"
        except (TypeError, ValueError):
            cik = path.stem.removeprefix("companyfacts-CIK")
        ticker = ticker_by_cik.get(cik, cik)
        issuer = _issuer_report(path, document, ticker)
        issuers.append(issuer)
        sha256[path.name] = issuer["sha256"]
    total_anomalies = sum(int(issuer["anomalies"]) for issuer in issuers)
    return {
        "schema_version": 1,
        "snapshot_date": snapshot_date,
        "generated_at": _now(),
        "cache_dir": str(cache),
        "issuer_count": len(issuers),
        "flow_metrics": list(FLOW_METRICS),
        "companyfacts_sha256": sha256,
        "issuers": issuers,
        "summary": {
            "issuers": len(issuers),
            "anomalies": total_anomalies,
            "restated_periods": sum(int(issuer["restated_periods"]) for issuer in issuers),
            "material_revisions": sum(int(issuer["material_revisions"]) for issuer in issuers),
            "form_fallback_periods": sum(
                int(issuer["form_fallback_periods"]) for issuer in issuers
            ),
        },
    }


def _md(value: Any) -> str:
    return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ")


def render_data_quality_markdown(report: Mapping[str, Any]) -> str:
    issuers = report.get("issuers", [])
    metrics = report.get("flow_metrics", [])
    lines = [
        "# SEC companyfacts data quality",
        "",
        f"Snapshot date: **{report.get('snapshot_date', '—')}**. Issuers: **{report.get('issuer_count', 0)}**. Checks use only the cached SEC companyfacts JSON; no network or live calls are used.",
        "",
        "A quarterly sum check runs when an annual fact and all four quarters are derivable. The tolerance is the larger of 0.5% of the annual value and $1 million. YTD monotonicity is checked only for metrics that cannot decrease within a year (revenue, gross profit, capex, R&D); income lines can legitimately fall after a loss quarter. Fiscal years and quarters are assigned from each period's own dates (SEC `fy`/`fp` describe the filing, not the period). Anomalies are consistency failures (quarterly sum ≠ annual, falling YTD totals) and non-statement-form fallbacks. Periods that later filings report with a different value are listed separately as revisions — routine reclassifications are common — and counted as material when the change exceeds 0.5%. Detail examples are capped at 12 per metric while counts remain complete.",
        "",
        "## Summary by issuer",
        "",
        "| Issuer | Ticker | Checks passed | Checks total | Anomalies | Revised periods | Material revisions | Form fallbacks |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for issuer in issuers if isinstance(issuers, list) else []:
        lines.append(
            f"| {_md(issuer.get('entity'))} | {_md(issuer.get('ticker'))} | {issuer.get('checks_passed', 0)} | {issuer.get('checks_total', 0)} | {issuer.get('anomalies', 0)} | {issuer.get('restated_periods', 0)} | {issuer.get('material_revisions', 0)} | {issuer.get('form_fallback_periods', 0)} |"
        )
    lines.extend(["", "## Metric coverage", ""])
    lines.append("| Issuer | " + " | ".join(str(metric) for metric in metrics) + " |")
    lines.append("|---|" + "---:|" * len(metrics))
    for issuer in issuers if isinstance(issuers, list) else []:
        metric_values = issuer.get("metrics", {})
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(issuer.get("ticker")),
                    *[
                        "available"
                        if isinstance(metric_values, Mapping)
                        and metric_values.get(metric, {}).get("available")
                        else "—"
                        for metric in metrics
                    ],
                ]
            )
            + " |"
        )
    lines.extend(["", "## Anomalies", ""])
    anomaly_rows = []
    for issuer in issuers if isinstance(issuers, list) else []:
        metric_values = issuer.get("metrics", {})
        for metric, value in metric_values.items() if isinstance(metric_values, Mapping) else []:
            for anomaly in value.get("anomalies", []) if isinstance(value, Mapping) else []:
                accessions = sorted(
                    {
                        str(anomaly.get(key))
                        for key in ("from_accn", "to_accn")
                        if anomaly.get(key)
                    }
                )
                for key in ("annual_accessions", "quarter_accessions", "accessions"):
                    accessions.extend(str(item) for item in anomaly.get(key, []) if item)
                anomaly_rows.append(
                    (
                        issuer.get("ticker"),
                        metric,
                        anomaly.get("type"),
                        anomaly.get("fiscal_year") or anomaly.get("start"),
                        sorted(set(accessions)),
                    )
                )
    if anomaly_rows:
        lines.extend(
            [
                "| Issuer | Metric | Type | Period | Accessions |",
                "|---|---|---|---|---|",
            ]
        )
        for ticker, metric, kind, period, accessions in anomaly_rows:
            lines.append(
                f"| {_md(ticker)} | {_md(metric)} | {_md(kind)} | {_md(period)} | {_md(', '.join(accessions))} |"
            )
    else:
        lines.append("No anomalies found in the cached snapshot.")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A passed arithmetic check does not make a filing correct; it only shows internal consistency between tagged facts. A restatement is not automatically an error, but it lowers evidence strength for verdicts that rely on the affected period. A form fallback means the selected period had no 10-K/10-Q statement-form row and should be treated as low strength.",
            "",
        ]
    )
    return "\n".join(lines)


def write_data_quality_artifacts(
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
    *,
    snapshot_date: str = DEFAULT_SNAPSHOT_DATE,
    report_path: str | Path = DEFAULT_REPORT_PATH,
    doc_path: str | Path = DEFAULT_DOC_PATH,
) -> dict[str, Any]:
    report = build_data_quality_report(cache_dir, snapshot_date=snapshot_date)
    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    doc_file = Path(doc_path)
    doc_file.parent.mkdir(parents=True, exist_ok=True)
    doc_file.write_text(render_data_quality_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--snapshot-date", default=DEFAULT_SNAPSHOT_DATE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC_PATH)
    args = parser.parse_args(argv)
    report = write_data_quality_artifacts(
        args.cache_dir,
        snapshot_date=args.snapshot_date,
        report_path=args.report,
        doc_path=args.doc,
    )
    print(
        json.dumps(
            {
                "snapshot_date": report["snapshot_date"],
                "issuer_count": report["issuer_count"],
                "report": str(args.report),
                "doc": str(args.doc),
            },
            indent=2,
        )
    )
    return 0


__all__ = [
    "DEFAULT_REPORT_PATH",
    "DEFAULT_SNAPSHOT_DATE",
    "FLOW_METRICS",
    "build_data_quality_report",
    "main",
    "render_data_quality_markdown",
    "write_data_quality_artifacts",
]

