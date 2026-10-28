#!/usr/bin/env python3
"""Build the labeled evaluation set from raw SEC companyfacts snapshots.

This file intentionally has no import from ``claimcheck``.  The evaluator's
gold path is a small, independent reader so a bug in the production EDGAR
client cannot silently label its own test set.

``claims.yaml`` is JSON-compatible YAML.  That keeps the checked-in dataset
readable by ordinary YAML tooling while allowing this script to run in the
minimal project virtualenv without adding a YAML dependency.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLAIMS = ROOT / "eval" / "claims.yaml"
DEFAULT_CACHE = ROOT / ".cache"
DEFAULT_JSONL = ROOT / "eval" / "claims.jsonl"
DEFAULT_FACTS = ROOT / "eval" / "gold_facts.json"
DEFAULT_REVIEW = ROOT / "eval" / "GOLD_REVIEW.md"

VALID_VERDICTS = {"supported", "contradicted", "insufficient_evidence"}
VALID_SPLITS = {"dev", "test"}
STATEMENT_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A", "20-F", "20-F/A", "40-F", "40-F/A"}
METRIC_ALIASES: dict[str, tuple[tuple[str, str], ...]] = {
    "revenue": (
        ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
        ("us-gaap", "Revenues"),
    ),
    "net_income": (("us-gaap", "NetIncomeLoss"),),
    "operating_income": (("us-gaap", "OperatingIncomeLoss"),),
    "gross_profit": (("us-gaap", "GrossProfit"),),
    "total_assets": (("us-gaap", "Assets"),),
    "cash": (
        ("us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
        ("us-gaap", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
    ),
    "capex": (("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"),),
    "rd_expense": (("us-gaap", "ResearchAndDevelopmentExpense"),),
    "eps_diluted": (("us-gaap", "EarningsPerShareDiluted"),),
}
SCALE_FACTORS = {"usd": 1.0, "million": 1_000_000.0, "billion": 1_000_000_000.0}
PERIOD_BASES = {"calendar", "fiscal", "month_named"}
PERIOD_RE = re.compile(r"^(?:(?P<fy>FY)(?P<fy_year>\d{4})|(?P<year>\d{4})(?P<quarter>Q[1-4]))$", re.I)
FISCAL_PERIOD_RE = re.compile(r"^FY(?P<year>\d{4})Q(?P<quarter>[1-4])$", re.I)
CALENDAR_YEAR_RE = re.compile(r"^(?:CY)?(?P<year>20\d{2})$", re.I)
FRAME_RE = re.compile(r"^CY(?P<year>\d{4})(?P<quarter>Q[1-4])(?:I)?$", re.I)


class GoldBuildError(RuntimeError):
    """Raised when the dataset or snapshot cannot produce deterministic gold."""


@dataclass(frozen=True)
class CompanySnapshot:
    ticker: str
    cik: str
    path: Path
    sha256: str
    document: dict[str, Any]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GoldBuildError(f"unable to read JSON {path}: {exc}") from exc


def load_claims(path: str | Path = DEFAULT_CLAIMS) -> list[dict[str, Any]]:
    """Load the JSON-compatible YAML dataset."""

    source = Path(path)
    value = _read_json(source)
    if isinstance(value, dict):
        value = value.get("claims")
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise GoldBuildError(f"{source} must contain a claims list")
    return [dict(item) for item in value]


def validate_claims(claims: Iterable[Mapping[str, Any]], *, strict: bool = True) -> None:
    items = list(claims)
    ids = [item.get("id") for item in items]
    if any(not isinstance(value, str) for value in ids) or len(set(ids)) != len(ids):
        raise GoldBuildError("claim ids must be unique strings")
    for item in items:
        if item.get("split") not in VALID_SPLITS:
            raise GoldBuildError(f"{item.get('id')}: split must be dev or test")
        if item.get("gold_verdict") not in VALID_VERDICTS:
            raise GoldBuildError(f"{item.get('id')}: invalid hand-written gold_verdict")
        if strict and (not isinstance(item.get("gold_note"), str) or not item["gold_note"].strip()):
            raise GoldBuildError(f"{item.get('id')}: gold_note must be a non-empty one-line explanation")
        if not isinstance(item.get("claim"), str) or not item["claim"].strip():
            raise GoldBuildError(f"{item.get('id')}: claim must be non-empty text")
        if not isinstance(item.get("spec"), dict):
            raise GoldBuildError(f"{item.get('id')}: spec must be an object")
    if strict:
        if len(items) != 30:
            raise GoldBuildError(f"expected 30 claims, found {len(items)}")
        expected_ids = [f"C{number:02d}" for number in range(1, 31)]
        if ids != expected_ids:
            raise GoldBuildError(f"expected ids C01..C30 in order, found {ids}")
        counts = {split: sum(item.get("split") == split for item in items) for split in VALID_SPLITS}
        if counts != {"dev": 20, "test": 10}:
            raise GoldBuildError(f"expected 20 dev and 10 test claims, found {counts}")
        categories = {str(item.get("category")) for item in items}
        expected = {
            "exact_value_true",
            "exact_value_false",
            "approximate",
            "inequality",
            "yoy_true",
            "yoy_false",
            "period_trap",
            "unit_trap",
            "multi_part",
            "record_first",
            "insufficient_evidence",
        }
        missing = sorted(expected - categories)
        if missing:
            raise GoldBuildError(f"missing required categories: {', '.join(missing)}")
        category_splits: dict[str, set[str]] = {}
        category_counts: dict[str, int] = {}
        for item in items:
            category = str(item.get("category"))
            category_splits.setdefault(category, set()).add(str(item.get("split")))
            category_counts[category] = category_counts.get(category, 0) + 1
        unstratified = sorted(
            category
            for category, count in category_counts.items()
            if count >= 2 and category_splits[category] != VALID_SPLITS
        )
        if unstratified:
            raise GoldBuildError(
                "categories with at least two claims must appear in both splits: "
                + ", ".join(unstratified)
            )


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def _load_ticker_map(cache_dir: Path) -> dict[str, str]:
    document = _read_json(cache_dir / "company_tickers.json")
    records: Iterable[Any]
    if isinstance(document, dict) and isinstance(document.get("data"), list):
        records = document["data"]
    elif isinstance(document, dict):
        records = document.values()
    else:
        records = []
    result: dict[str, str] = {}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        ticker = str(record.get("ticker") or "").strip().upper()
        if not ticker:
            continue
        try:
            result[ticker] = f"{int(record.get('cik_str')):010d}"
        except (TypeError, ValueError):
            continue
    return result


def load_snapshot(cache_dir: str | Path, ticker: str, ticker_map: Mapping[str, str]) -> CompanySnapshot:
    normalized = str(ticker).strip().upper()
    try:
        cik = ticker_map[normalized]
    except KeyError as exc:
        raise GoldBuildError(f"{normalized}: ticker not found in company_tickers.json") from exc
    path = Path(cache_dir) / f"companyfacts-CIK{cik}.json"
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise GoldBuildError(f"{normalized}: missing snapshot {path}: {exc}") from exc
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoldBuildError(f"{normalized}: invalid snapshot {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise GoldBuildError(f"{normalized}: snapshot is not an object")
    return CompanySnapshot(normalized, cik, path, _sha256(raw), document)


def _as_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _duration_days(fact: Mapping[str, Any]) -> int | None:
    start = _as_date(fact.get("start"))
    end = _as_date(fact.get("end"))
    if start is None or end is None:
        return None
    return (end - start).days + 1


def _period_type(fact: Mapping[str, Any]) -> str:
    duration = _duration_days(fact)
    if duration is None:
        return "instant"
    if 80 <= duration <= 100:
        return "quarter"
    if 300 <= duration <= 380:
        return "annual"
    return "ytd"


def _frame_period(fact: Mapping[str, Any]) -> str | None:
    match = FRAME_RE.match(str(fact.get("frame") or ""))
    if not match:
        return None
    return f"{match.group('year')}{match.group('quarter').upper()}"


def _period_label(fact: Mapping[str, Any]) -> str | None:
    frame = _frame_period(fact)
    if frame and _period_type(fact) == "quarter":
        return frame
    end = _as_date(fact.get("end"))
    period_type = _period_type(fact)
    if end is None:
        return None
    if period_type == "quarter":
        return f"{end.year}Q{((end.month - 1) // 3) + 1}"
    if period_type == "annual":
        return f"FY{end.year}"
    return None


def _fiscal_period_parts(period: str) -> tuple[int, int] | None:
    match = FISCAL_PERIOD_RE.match(str(period).upper())
    if not match:
        return None
    return int(match.group("year")), int(match.group("quarter"))


def _calendar_period_parts(period: str) -> tuple[int, int] | None:
    normalized = str(period).upper().removeprefix("CY")
    match = re.fullmatch(r"(20\d{2})Q([1-4])", normalized)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _period_from_spec(spec: Mapping[str, Any]) -> str:
    """Return the canonical period label, including explicit fiscal quarters.

    Fiscal quarters may be written as ``FY2025Q3`` or as the structured
    ``fiscal_year``/``fiscal_quarter`` pair.  The latter is useful to callers
    constructing specs programmatically; both forms resolve through the
    issuer's SEC ``fy``/``fp`` fields rather than calendar dates.
    """

    period_value = spec.get("period")
    fiscal_period_value = spec.get("fiscal_period")
    if fiscal_period_value is not None and period_value is None:
        period_value = fiscal_period_value

    fiscal_year = spec.get("fiscal_year")
    fiscal_quarter = spec.get("fiscal_quarter")
    if fiscal_year is not None or fiscal_quarter is not None:
        if isinstance(fiscal_year, bool) or not isinstance(fiscal_year, (int, str)):
            raise GoldBuildError("fiscal_year must be a four-digit year")
        year_text = str(fiscal_year).upper()
        if year_text.startswith("FY"):
            year_text = year_text[2:]
        if not re.fullmatch(r"\d{4}", year_text):
            raise GoldBuildError("fiscal_year must be a four-digit year")
        quarter_text = str(fiscal_quarter or "").upper()
        if quarter_text.startswith("Q"):
            quarter_text = quarter_text[1:]
        if quarter_text not in {"1", "2", "3", "4"}:
            raise GoldBuildError("fiscal_quarter must be Q1, Q2, Q3, or Q4")
        derived_period = f"FY{year_text}Q{quarter_text}"
        if period_value is not None and str(period_value).upper() != derived_period:
            raise GoldBuildError("period and fiscal year/quarter disagree")
        period_value = derived_period

    return str(period_value or "").upper()


def _period_basis(spec: Mapping[str, Any]) -> str:
    """Return the explicit period basis, with a backwards-compatible default.

    v1 specs predate ``period_basis``.  Their canonical ``FY...`` labels are
    fiscal and their bare ``YYYYQn`` labels are calendar, so that inference is
    safe for the old dataset while v2 can require an explicit basis in every
    generated spec.
    """

    value = spec.get("period_basis")
    if value is None or str(value).strip() == "":
        period = _period_from_spec(spec)
        return "fiscal" if period.startswith("FY") else "calendar"
    basis = str(value).strip().lower()
    if basis not in PERIOD_BASES:
        raise GoldBuildError(
            f"period_basis must be one of {', '.join(sorted(PERIOD_BASES))}, got {value!r}"
        )
    return basis


def _fiscal_year_end(snapshot: CompanySnapshot) -> date | None:
    """Infer an issuer's fiscal year-end from its annual SEC facts."""

    ends: list[date] = []
    for metric in METRIC_ALIASES:
        try:
            candidates = _facts_for_metric(snapshot, metric)
        except GoldBuildError:
            continue
        for _concept, _unit, fact in candidates:
            if str(fact.get("fp") or "").upper() != "FY":
                continue
            if _period_type(fact) != "annual":
                continue
            end = _as_date(fact.get("end"))
            if end is not None:
                ends.append(end)
    if not ends:
        return None
    # The latest period end is the most useful signal; duplicate comparative
    # facts are harmless because they have the same date.
    return max(ends)


def is_non_calendar_issuer(snapshot: CompanySnapshot) -> bool:
    """Whether the issuer's fiscal year-end is outside Dec 31 +/- 7 days."""

    end = _fiscal_year_end(snapshot)
    if end is None:
        return False
    nearest_december_end = min(
        (date(end.year - 1, 12, 31), date(end.year, 12, 31), date(end.year + 1, 12, 31)),
        key=lambda candidate: abs((end - candidate).days),
    )
    return abs((end - nearest_december_end).days) > 7


def _period_display(period: str) -> str:
    fiscal_parts = _fiscal_period_parts(period)
    if fiscal_parts is not None:
        year, quarter = fiscal_parts
        return f"fiscal Q{quarter} {year}"
    return period


def _date_range(record: Mapping[str, Any]) -> str | None:
    start = record.get("start")
    end = record.get("end")
    if isinstance(start, str) and isinstance(end, str):
        return f"{start}..{end}"
    if isinstance(end, str):
        return end
    return None


def _filed_key(fact: Mapping[str, Any]) -> tuple[str, str]:
    return (str(fact.get("filed") or ""), str(fact.get("accn") or ""))


def _facts_for_metric(snapshot: CompanySnapshot, metric: str) -> list[tuple[str, str, dict[str, Any]]]:
    aliases = METRIC_ALIASES.get(metric)
    if aliases is None:
        raise GoldBuildError(f"unsupported gold metric: {metric}")
    facts_root = snapshot.document.get("facts", {})
    all_candidates: list[tuple[str, str, dict[str, Any]]] = []
    for namespace, concept in aliases:
        concept_data = facts_root.get(namespace, {}).get(concept, {})
        units = concept_data.get("units", {}) if isinstance(concept_data, dict) else {}
        candidates: list[tuple[str, str, dict[str, Any]]] = []
        for unit, values in units.items():
            if not isinstance(values, list):
                continue
            for fact in values:
                if not isinstance(fact, dict):
                    continue
                if str(fact.get("form") or "").upper() not in STATEMENT_FORMS:
                    continue
                value = fact.get("val")
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    continue
                candidates.append((concept, str(unit), fact))
        all_candidates.extend(candidates)
    return all_candidates


def _quarter_end(period: str) -> date | None:
    parts = _calendar_period_parts(period)
    if parts is None:
        return None
    year, quarter = parts
    month = quarter * 3
    if month == 12:
        return date(year, 12, 31)
    next_month = month + 1
    return date(year, next_month, 1).fromordinal(date(year, next_month, 1).toordinal() - 1)


def _same_calendar_quarter(fact: Mapping[str, Any], period: str) -> bool:
    end = _as_date(fact.get("end"))
    target_end = _quarter_end(period)
    normalized = str(period).upper().removeprefix("CY")
    frame = _frame_period(fact)
    # SEC's CY frame is the authoritative calendar interpretation for
    # 52/53-week issuers.  Its quarter can end in the following month (for
    # example, NVIDIA's calendar Q2 2024 frame ends July 28).
    if _period_type(fact) == "quarter" and frame == normalized:
        return True
    return _period_type(fact) == "quarter" and end == target_end


def _select_fact(
    snapshot: CompanySnapshot,
    metric: str,
    period: str,
    *,
    basis: str = "sec",
) -> tuple[str, str, dict[str, Any]] | None:
    basis = str(basis or "sec").lower()
    if basis not in {"sec", *PERIOD_BASES}:
        raise GoldBuildError(f"unknown period basis {basis!r}")
    normalized_period = str(period).upper()
    if basis in {"fiscal", "month_named"}:
        calendar_parts = _calendar_period_parts(normalized_period)
        if calendar_parts is not None:
            normalized_period = f"FY{calendar_parts[0]}Q{calendar_parts[1]}"
        elif re.fullmatch(r"20\d{2}", normalized_period):
            normalized_period = f"FY{normalized_period}"
    elif basis == "calendar":
        fiscal_parts_from_label = _fiscal_period_parts(normalized_period)
        if fiscal_parts_from_label is not None:
            normalized_period = f"{fiscal_parts_from_label[0]}Q{fiscal_parts_from_label[1]}"
        elif re.fullmatch(r"FY20\d{2}", normalized_period):
            normalized_period = normalized_period[2:]
    candidates = _facts_for_metric(snapshot, metric)
    aliases = METRIC_ALIASES[metric]
    fiscal_parts = _fiscal_period_parts(normalized_period)
    calendar_year_match = CALENDAR_YEAR_RE.fullmatch(normalized_period)

    if basis == "calendar" and calendar_year_match is not None:
        calendar_year = int(calendar_year_match.group("year"))
        direct: list[tuple[str, str, dict[str, Any]]] = []
        for concept, unit, fact in candidates:
            end = _as_date(fact.get("end"))
            if (
                end is not None
                and end.year == calendar_year
                and end.month == 12
                and end.day >= 24
                and _period_type(fact) in {"annual", "instant"}
                and str(fact.get("fp") or "").upper() == "FY"
            ):
                direct.append((concept, unit, fact))
        if direct:
            return max(direct, key=lambda item: (_as_date(item[2].get("end")) or date.min, _filed_key(item[2])))

        # SEC often exposes calendar-year frames only as four calendar
        # quarters for non-calendar issuers.  Derive a calendar flow year so
        # an ambiguous annual claim has two real readings as well.
        if metric in {"revenue", "net_income", "operating_income", "gross_profit", "capex", "rd_expense"}:
            quarter_parts = [(calendar_year, quarter) for quarter in range(1, 5)]
            selected_quarters = [
                _select_fact(snapshot, metric, f"{year}Q{quarter}", basis="calendar")
                for year, quarter in quarter_parts
            ]
            if all(item is not None for item in selected_quarters):
                first = selected_quarters[0]
                assert first is not None
                concept, unit, _first_fact = first
                facts = [item[2] for item in selected_quarters if item is not None]
                derived = {
                    "val": sum(float(fact["val"]) for fact in facts),
                    "start": date(calendar_year, 1, 1).isoformat(),
                    "end": date(calendar_year, 12, 31).isoformat(),
                    "accn": facts[-1].get("accn"),
                    "form": "derived",
                    "filed": max(str(fact.get("filed") or "") for fact in facts),
                    "frame": f"CY{calendar_year}",
                    "fy": calendar_year,
                    "fp": "FY",
                    "derived": True,
                    "derivation": "calendar Q1 + Q2 + Q3 + Q4",
                    "_component_specs": [
                        ("calendar_component", f"{calendar_year}Q{quarter}", selected)
                        for quarter, selected in enumerate(selected_quarters, 1)
                        if selected is not None
                    ],
                }
                return concept, unit, derived
        return None

    for _namespace, preferred_concept in aliases:
        matches: list[tuple[str, str, dict[str, Any]]] = []
        for concept, unit, fact in candidates:
            if concept != preferred_concept:
                continue
            if fiscal_parts is not None and basis != "calendar":
                fiscal_year, fiscal_quarter = fiscal_parts
                fact_year = fact.get("fy")
                try:
                    fact_year = int(fact_year)
                except (TypeError, ValueError):
                    fact_year = None
                if (
                    _period_type(fact) in {"quarter", "instant"}
                    and fact_year == fiscal_year
                    and str(fact.get("fp") or "").upper() == f"Q{fiscal_quarter}"
                ):
                    matches.append((concept, unit, fact))
                continue
            if basis == "calendar" and normalized_period.startswith("20") and "Q" in normalized_period:
                if _same_calendar_quarter(fact, normalized_period):
                    matches.append((concept, unit, fact))
                continue
            if (
                normalized_period.startswith("FY")
                and re.fullmatch(r"FY\d{4}", normalized_period)
                and str(fact.get("fp") or "").upper() == "FY"
            ):
                try:
                    fact_year = int(fact.get("fy"))
                except (TypeError, ValueError):
                    fact_year = None
                if fact_year == int(normalized_period[2:]) and _period_type(fact) in {"annual", "instant"}:
                    matches.append((concept, unit, fact))
                continue
            if _period_label(fact) == normalized_period:
                matches.append((concept, unit, fact))
        if matches:
            if fiscal_parts is not None or re.fullmatch(r"FY\d{4}", normalized_period):
                # A filing can carry the prior-year comparative with the same
                # fy/fp values. The latest period end is the issuer's actual
                # fiscal period; later filings win ties for restatements.
                return max(
                    matches,
                    key=lambda item: (
                        _as_date(item[2].get("end")) or date.min,
                        _filed_key(item[2]),
                    ),
                )
            return max(matches, key=lambda item: _filed_key(item[2]))
        calendar_parts = _calendar_period_parts(normalized_period)
        if basis == "calendar" and calendar_parts is not None:
            calendar_year, _calendar_quarter = calendar_parts
            target_end = _quarter_end(normalized_period)
            for fiscal_year in (calendar_year - 1, calendar_year, calendar_year + 1):
                derived = _select_fiscal_q4_candidate(snapshot, metric, fiscal_year, preferred_concept)
                if derived is not None and _as_date(derived[2].get("end")) == target_end:
                    return derived
        if fiscal_parts is not None and fiscal_parts[1] == 4 and basis != "calendar":
            derived = _select_fiscal_q4_candidate(snapshot, metric, fiscal_parts[0], preferred_concept)
            if derived is not None:
                return derived
    return None


def _fact_record(
    snapshot: CompanySnapshot,
    metric: str,
    period: str,
    selected: tuple[str, str, dict[str, Any]] | None,
    *,
    role: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "ticker": snapshot.ticker,
        "cik": snapshot.cik,
        "metric": metric,
        "period": period,
        "role": role,
        "value": None,
        "concept": None,
        "unit": None,
        "start": None,
        "end": None,
        "accn": None,
        "form": None,
        "filed": None,
        "frame": None,
        "period_type": None,
        "source_sha256": snapshot.sha256,
        "source_file": snapshot.path.name,
    }
    if selected is None:
        return record
    concept, unit, fact = selected
    record.update(
        {
            "value": fact.get("val"),
            "concept": concept,
            "unit": unit,
            "start": fact.get("start"),
            "end": fact.get("end"),
            "accn": fact.get("accn"),
            "form": fact.get("form"),
            "filed": fact.get("filed"),
            "frame": fact.get("frame"),
            "period_type": _period_type(fact),
        }
    )
    if fact.get("derived"):
        record["derived"] = True
        record["derivation"] = fact.get("derivation")
    component_specs = fact.get("_component_specs")
    if isinstance(component_specs, list):
        record["components"] = [
            _fact_record(snapshot, metric, component_period, selected_component, role=component_role)
            for component_role, component_period, selected_component in component_specs
        ]
    return record


def _select_fiscal_q4_candidate(
    snapshot: CompanySnapshot,
    metric: str,
    fiscal_year: int,
    preferred_concept: str,
) -> tuple[str, str, dict[str, Any]] | None:
    """Derive an issuer fiscal Q4 from the annual and 9M SEC facts."""

    candidates = [
        item for item in _facts_for_metric(snapshot, metric) if item[0] == preferred_concept
    ]
    annuals: list[tuple[str, str, dict[str, Any]]] = []
    ytd_candidates: list[tuple[str, str, dict[str, Any]]] = []
    for concept, unit, fact in candidates:
        fact_year = fact.get("fy")
        try:
            fact_year = int(fact_year)
        except (TypeError, ValueError):
            fact_year = None
        if fact_year != fiscal_year:
            continue
        fp = str(fact.get("fp") or "").upper()
        if fp == "FY" and _period_type(fact) == "annual":
            annuals.append((concept, unit, fact))
        elif fp == "Q3" and _period_type(fact) == "ytd" and 250 <= (_duration_days(fact) or 0) <= 290:
            ytd_candidates.append((concept, unit, fact))

    for annual in sorted(
        annuals,
        key=lambda item: (_as_date(item[2].get("end")) or date.min, _filed_key(item[2])),
        reverse=True,
    ):
        annual_fact = annual[2]
        annual_start = str(annual_fact.get("start") or "")
        matching_ytd = [item for item in ytd_candidates if str(item[2].get("start") or "") == annual_start]
        if not matching_ytd:
            continue
        ytd = max(matching_ytd, key=lambda item: _filed_key(item[2]))
        ytd_fact = ytd[2]
        ytd_end = _as_date(ytd_fact.get("end"))
        annual_end = _as_date(annual_fact.get("end"))
        if ytd_end is None or annual_end is None or annual_end <= ytd_end:
            continue
        derived = {
            "val": annual_fact["val"] - ytd_fact["val"],
            "start": (ytd_end.fromordinal(ytd_end.toordinal() + 1)).isoformat(),
            "end": annual_end.isoformat(),
            "accn": annual_fact.get("accn"),
            "form": "derived",
            "filed": max(str(annual_fact.get("filed") or ""), str(ytd_fact.get("filed") or "")),
            "frame": None,
            "fy": fiscal_year,
            "fp": "Q4",
            "derived": True,
            "derivation": "annual - 9M YTD",
            "_component_specs": [
                ("annual_component", f"FY{fiscal_year}", annual),
                ("ytd_component", f"FY{fiscal_year}Q3", ytd),
            ],
        }
        return annual[0], annual[1], derived
    return None


def _scale_factor(spec: Mapping[str, Any]) -> float:
    scale = str(spec.get("scale") or "usd").lower()
    try:
        return SCALE_FACTORS[scale]
    except KeyError as exc:
        raise GoldBuildError(f"unknown number scale {scale!r}") from exc


def _stated_base(spec: Mapping[str, Any]) -> float:
    stated = spec.get("stated")
    if isinstance(stated, bool) or not isinstance(stated, (int, float)):
        raise GoldBuildError("a SEC value spec needs numeric stated")
    return float(stated) * _scale_factor(spec)


def _selection_basis(spec: Mapping[str, Any]) -> str:
    basis = _period_basis(spec)
    return "fiscal" if basis in {"fiscal", "month_named"} else "calendar"


def _fmt_number(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and value.is_integer():
        return f"{int(value):,}"
    if isinstance(value, (int, float)):
        return f"{value:,.3f}".rstrip("0").rstrip(".")
    return str(value)


def _fmt_usd(value: Any) -> str:
    if value is None:
        return "—"
    amount = float(value)
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    if amount >= 1_000_000_000:
        return f"{sign}${amount / 1_000_000_000:.3f}B"
    if amount >= 1_000_000:
        return f"{sign}${amount / 1_000_000:.3f}M"
    return f"{sign}${amount:,.2f}"


def _fact_is_present(record: Mapping[str, Any]) -> bool:
    return record.get("concept") is not None and isinstance(record.get("value"), (int, float))


def _value_part(spec: Mapping[str, Any], snapshots: Mapping[str, CompanySnapshot]) -> dict[str, Any]:
    ticker = str(spec.get("ticker") or "").upper()
    metric = str(spec.get("metric") or "").lower()
    period = _period_from_spec(spec)
    snapshot = snapshots[ticker]
    selected = _select_fact(snapshot, metric, period, basis=_selection_basis(spec))
    record = _fact_record(snapshot, metric, period, selected)
    if not _fact_is_present(record):
        return {
            "truth": None,
            "facts": [record],
            "note": f"SEC snapshot has no {ticker} {metric} fact for {period}; the claim cannot be checked.",
        }
    actual = float(record["value"])
    stated = _stated_base(spec)
    comparator = str(spec.get("comparator") or "eq").lower()
    if comparator == "eq":
        precision = spec.get("precision")
        if not isinstance(precision, (int, float)) or precision <= 0:
            raise GoldBuildError(f"{ticker} {metric} {period}: eq requires positive precision")
        tolerance = float(precision) * _scale_factor(spec) / 2.0
        truth = abs(actual - stated) <= tolerance + 1e-6
        comparison = f"rounds to {_fmt_number(float(spec['stated']))} {spec.get('scale', 'usd')}"
    elif comparator in {"gt", "gte", "lt", "lte"}:
        truth = {
            "gt": actual > stated,
            "gte": actual >= stated,
            "lt": actual < stated,
            "lte": actual <= stated,
        }[comparator]
        comparison = f"{comparator} {_fmt_usd(stated)}"
    elif comparator == "approx":
        tolerance_pct = spec.get("tolerance_pct")
        if not isinstance(tolerance_pct, (int, float)) or tolerance_pct < 0:
            raise GoldBuildError(f"{ticker} {metric} {period}: approx requires tolerance_pct")
        denominator = max(abs(stated), 1.0)
        truth = abs(actual - stated) / denominator <= float(tolerance_pct) / 100.0 + 1e-12
        comparison = f"within {float(tolerance_pct):g}% of {_fmt_usd(stated)}"
    else:
        raise GoldBuildError(f"unsupported comparator {comparator!r}")
    period_label = _period_display(period)
    date_range = _date_range(record)
    period_label = f"{period_label} ({date_range})" if date_range and _fiscal_period_parts(period) else period_label
    facts = [record]
    comparison_note = ""
    comparison_period_value = spec.get("comparison_period")
    if comparison_period_value is not None:
        comparison_period = _period_from_spec({"period": comparison_period_value})
        comparison_selected = _select_fact(snapshot, metric, comparison_period, basis=_selection_basis(spec))
        comparison_record = _fact_record(snapshot, metric, comparison_period, comparison_selected, role="comparison")
        facts.append(comparison_record)
        if _fact_is_present(comparison_record):
            comparison_label = _period_display(comparison_period)
            comparison_dates = _date_range(comparison_record)
            if comparison_dates:
                comparison_label = f"{comparison_label} ({comparison_dates})"
            comparison_note = f"; {comparison_label} reports {_fmt_usd(comparison_record['value'])}"
    note = (
        f"SEC {period_label} reports {_fmt_usd(actual)}{comparison_note}; stated {_fmt_usd(stated)} and {comparison} "
        f"({record.get('concept')}, {record.get('accn') or 'no accession'})."
    )
    return {"truth": bool(truth), "facts": facts, "note": note}


def _growth_part(spec: Mapping[str, Any], snapshots: Mapping[str, CompanySnapshot]) -> dict[str, Any]:
    ticker = str(spec.get("ticker") or "").upper()
    metric = str(spec.get("metric") or "").lower()
    period = _period_from_spec(spec)
    base_period = _period_from_spec({"period": spec.get("base_period")})
    snapshot = snapshots[ticker]
    selection_basis = _selection_basis(spec)
    current = _select_fact(snapshot, metric, period, basis=selection_basis)
    prior = _select_fact(snapshot, metric, base_period, basis=str(spec.get("base_period_basis") or selection_basis))
    current_record = _fact_record(snapshot, metric, period, current, role="current")
    prior_record = _fact_record(snapshot, metric, base_period, prior, role="base")
    if not _fact_is_present(current_record) or not _fact_is_present(prior_record):
        return {
            "truth": None,
            "facts": [current_record, prior_record],
            "note": f"SEC snapshot is missing one of {ticker} {metric} {period}/{base_period}; the change cannot be checked.",
        }
    current_value = float(current_record["value"])
    prior_value = float(prior_record["value"])
    if prior_value == 0:
        return {
            "truth": None,
            "facts": [current_record, prior_record],
            "note": f"SEC {base_period} value is zero, so the {period} YoY change is undefined.",
        }
    actual_pct = (current_value / prior_value - 1.0) * 100.0
    stated = spec.get("stated")
    if isinstance(stated, bool) or not isinstance(stated, (int, float)):
        raise GoldBuildError(f"{ticker} {metric} {period}: growth requires numeric stated")
    signed_stated = float(stated) * (-1.0 if str(spec.get("direction") or "").lower() in {"down", "fell", "decreased"} else 1.0)
    precision = float(spec.get("precision") or 1.0)
    truth = abs(actual_pct - signed_stated) <= precision / 2.0 + 1e-9
    note = (
        f"SEC {period} {_fmt_usd(current_value)} versus {base_period} {_fmt_usd(prior_value)} "
        f"is {actual_pct:+.1f}% YoY; stated {signed_stated:+.1f}% "
        f"({current_record.get('accn') or 'no accession'}; {prior_record.get('accn') or 'no accession'})."
    )
    return {"truth": bool(truth), "facts": [current_record, prior_record], "note": note}


def _all_quarter_records(snapshot: CompanySnapshot, metric: str) -> list[dict[str, Any]]:
    candidates = _facts_for_metric(snapshot, metric)
    by_period: dict[str, tuple[str, str, dict[str, Any]]] = {}
    annual_by_start: dict[str, tuple[str, str, dict[str, Any]]] = {}
    ytd_by_start: dict[str, tuple[str, str, dict[str, Any]]] = {}
    for concept, unit, fact in candidates:
        candidate = (concept, unit, fact)
        period_type = _period_type(fact)
        if period_type == "quarter":
            label = _period_label(fact)
            if label is None:
                continue
            current = by_period.get(label)
            if current is None or _filed_key(fact) > _filed_key(current[2]):
                by_period[label] = candidate
        elif period_type == "annual":
            start = str(fact.get("start") or "")
            current = annual_by_start.get(start)
            if start and (current is None or _filed_key(fact) > _filed_key(current[2])):
                annual_by_start[start] = candidate
        elif period_type == "ytd" and 250 <= (_duration_days(fact) or 0) <= 290:
            start = str(fact.get("start") or "")
            current = ytd_by_start.get(start)
            if start and (current is None or _filed_key(fact) > _filed_key(current[2])):
                ytd_by_start[start] = candidate
    records = [
        _fact_record(snapshot, metric, period, selected)
        for period, selected in sorted(by_period.items(), key=lambda item: item[0])
    ]
    for start, annual in annual_by_start.items():
        ytd = ytd_by_start.get(start)
        if ytd is None:
            continue
        annual_fact = annual[2]
        ytd_fact = ytd[2]
        annual_end = _as_date(annual_fact.get("end"))
        ytd_end = _as_date(ytd_fact.get("end"))
        if annual_end is None or ytd_end is None or annual_end <= ytd_end:
            continue
        q4_year = annual_end.year if annual_end.month >= 4 else annual_end.year - 1
        period = f"{q4_year}Q4"
        if period in by_period:
            continue
        derived_value = float(annual_fact["val"]) - float(ytd_fact["val"])
        derived = {
            "ticker": snapshot.ticker,
            "cik": snapshot.cik,
            "metric": metric,
            "period": period,
            "role": "derived_q4",
            "value": derived_value,
            "concept": annual[0],
            "unit": annual[1],
            "start": (ytd_end.fromordinal(ytd_end.toordinal() + 1)).isoformat(),
            "end": annual_end.isoformat(),
            "accn": annual_fact.get("accn"),
            "form": "derived",
            "filed": max(str(annual_fact.get("filed") or ""), str(ytd_fact.get("filed") or "")),
            "frame": None,
            "period_type": "quarter",
            "derived": True,
            "derivation": "annual - 9M YTD",
            "components": [
                _fact_record(snapshot, metric, f"FY{annual_end.year}", annual, role="annual_component"),
                _fact_record(snapshot, metric, f"{q4_year}Q3", ytd, role="ytd_component"),
            ],
            "source_sha256": snapshot.sha256,
            "source_file": snapshot.path.name,
        }
        records.append(derived)
    return records


def _first_time_part(spec: Mapping[str, Any], snapshots: Mapping[str, CompanySnapshot]) -> dict[str, Any]:
    ticker = str(spec.get("ticker") or "").upper()
    metric = str(spec.get("metric") or "").lower()
    period = _period_from_spec(spec)
    snapshot = snapshots[ticker]
    target_selected = _select_fact(snapshot, metric, period, basis=_selection_basis(spec))
    target = _fact_record(snapshot, metric, period, target_selected, role="target")
    if not _fact_is_present(target):
        return {
            "truth": None,
            "facts": [target],
            "note": f"SEC snapshot has no {ticker} {metric} fact for {period}; the first-time claim cannot be checked.",
        }
    threshold = float(spec.get("threshold")) * _scale_factor(spec)
    target_end = _as_date(target.get("end"))
    history = _all_quarter_records(snapshot, metric)
    prior = [
        item
        for item in history
        if target_end is not None
        and _as_date(item.get("end")) is not None
        and _as_date(item.get("end")) < target_end
        and isinstance(item.get("value"), (int, float))
    ]
    prior_above = [item for item in prior if float(item["value"]) > threshold]
    truth = float(target["value"]) > threshold and not prior_above
    prior_high = max((float(item["value"]) for item in prior), default=None)
    prior_high_record = max(prior, key=lambda item: float(item["value"])) if prior else None
    facts_used = [target]
    if prior_high_record is not None:
        facts_used.append(prior_high_record)
    note = (
        f"SEC {period} reports {_fmt_usd(target['value'])}; it is "
        f"the first quarter above {_fmt_usd(threshold)} through that period "
        f"(prior quarterly high {_fmt_usd(prior_high)}; {target.get('accn') or 'no accession'})."
    )
    return {"truth": bool(truth), "facts": facts_used, "note": note}


def _select_fiscal_duration_fact(
    snapshot: CompanySnapshot,
    metric: str,
    period: str,
    duration_kind: str,
) -> tuple[str, str, dict[str, Any]] | None:
    """Select a fiscal quarter, YTD, or annual fact for period-trap claims."""

    normalized = str(period).upper()
    parts = _fiscal_period_parts(normalized)
    candidates = _facts_for_metric(snapshot, metric)
    matches: list[tuple[str, str, dict[str, Any]]] = []
    for concept, unit, fact in candidates:
        fp = str(fact.get("fp") or "").upper()
        fact_year = fact.get("fy")
        try:
            fact_year = int(fact_year)
        except (TypeError, ValueError):
            fact_year = None
        if parts is not None:
            year, quarter = parts
            if fact_year != year or fp != f"Q{quarter}":
                continue
            period_type = _period_type(fact)
            days = _duration_days(fact) or 0
            if duration_kind == "quarter" and period_type in {"quarter", "instant"}:
                matches.append((concept, unit, fact))
            elif duration_kind == "ytd" and 100 < days < 380:
                matches.append((concept, unit, fact))
            continue
        if duration_kind == "annual" and fp == "FY" and _period_type(fact) == "annual":
            if _period_label(fact) == normalized:
                matches.append((concept, unit, fact))
    if not matches:
        return None
    return max(matches, key=lambda item: (_as_date(item[2].get("end")) or date.min, _filed_key(item[2])))


def _ambiguous_period_part(spec: Mapping[str, Any], snapshots: Mapping[str, CompanySnapshot]) -> dict[str, Any]:
    """Evaluate an intentionally unqualified period under both readings."""

    ticker = str(spec.get("ticker") or "").upper()
    metric = str(spec.get("metric") or "").lower()
    raw_period = _period_from_spec(spec)
    fiscal_period = _period_from_spec({"period": spec.get("fiscal_period") or raw_period})
    fiscal_parts = _fiscal_period_parts(fiscal_period)
    calendar_parts = _calendar_period_parts(fiscal_period)
    if fiscal_parts is None and calendar_parts is not None:
        fiscal_period = f"FY{calendar_parts[0]}Q{calendar_parts[1]}"
    if fiscal_parts is None:
        year_match = re.fullmatch(r"(?:FY)?(20\d{2})", fiscal_period)
        if year_match:
            fiscal_period = f"FY{year_match.group(1)}"
    fiscal_parts = _fiscal_period_parts(fiscal_period)
    if fiscal_parts is not None:
        calendar_period = f"{fiscal_parts[0]}Q{fiscal_parts[1]}"
    else:
        annual_match = re.fullmatch(r"FY(20\d{2})", fiscal_period)
        if annual_match:
            calendar_period = annual_match.group(1)
        else:
            calendar_period = str(spec.get("calendar_period") or raw_period).upper()

    fiscal_spec = dict(spec)
    fiscal_spec.update({"kind": "value", "period": fiscal_period, "period_basis": "fiscal"})
    calendar_spec = dict(spec)
    calendar_spec.update({"kind": "value", "period": calendar_period, "period_basis": "calendar"})
    fiscal_eval = _value_part(fiscal_spec, snapshots)
    calendar_eval = _value_part(calendar_spec, snapshots)
    fiscal_truth = fiscal_eval.get("truth")
    calendar_truth = calendar_eval.get("truth")
    truth = fiscal_truth if fiscal_truth == calendar_truth else None

    def verdict(value: Any) -> str:
        if value is True:
            return "supported"
        if value is False:
            return "contradicted"
        return "insufficient_evidence"

    def reading_value(evaluated: Mapping[str, Any]) -> str:
        for fact in evaluated.get("facts", []):
            if isinstance(fact, Mapping) and _fact_is_present(fact):
                return _fmt_usd(fact.get("value"))
        return "no matching SEC fact"

    fiscal_label = _period_display(fiscal_period)
    calendar_label = f"calendar {calendar_period}"
    note = (
        f"Ambiguous period readings: fiscal reading {fiscal_label} reports {reading_value(fiscal_eval)} "
        f"({verdict(fiscal_truth)}); {calendar_label} reports {reading_value(calendar_eval)} "
        f"({verdict(calendar_truth)})."
    )
    if fiscal_truth != calendar_truth:
        note += " The readings differ, so this claim is insufficient_evidence."
    else:
        note += f" Both readings yield {verdict(truth)}."
    return {
        "truth": truth,
        "facts": [*fiscal_eval.get("facts", []), *calendar_eval.get("facts", [])],
        "note": note,
        "readings": {"fiscal": fiscal_eval, "calendar": calendar_eval},
    }


def _period_trap_part(spec: Mapping[str, Any], snapshots: Mapping[str, CompanySnapshot]) -> dict[str, Any]:
    ticker = str(spec.get("ticker") or "").upper()
    metric = str(spec.get("metric") or "").lower()
    period = _period_from_spec(spec)
    snapshot = snapshots[ticker]

    trap_type = str(spec.get("trap_type") or "").lower()
    if trap_type in {
        "ytd_as_quarter",
        "ytd_correct",
        "annual_as_quarter",
        "annual_correct",
    }:
        quarter_period = _period_from_spec({"period": spec.get("quarter_period") or period})
        claimed_selected = _select_fiscal_duration_fact(snapshot, metric, quarter_period, "quarter")
        source_kind = "ytd" if trap_type.startswith("ytd") else "annual"
        source_period = (
            quarter_period
            if source_kind == "ytd"
            else _period_from_spec({"period": spec.get("annual_period") or f"FY{quarter_period[-6:-2]}"})
        )
        source_selected = _select_fiscal_duration_fact(snapshot, metric, source_period, source_kind)
        claimed_record = _fact_record(snapshot, metric, quarter_period, claimed_selected, role="claimed_period")
        source_record = _fact_record(snapshot, metric, source_period, source_selected, role=source_kind)
        if not _fact_is_present(source_record):
            return {
                "truth": None,
                "facts": [claimed_record, source_record],
                "note": f"SEC snapshot is missing the {source_kind} fact for {ticker} {quarter_period}.",
            }
        stated = _stated_base(spec)
        precision = float(spec.get("precision") or 0.0) * _scale_factor(spec)
        value_truth = abs(float(source_record["value"]) - stated) <= precision / 2.0 + 1e-6
        basis_truth = trap_type.endswith("_correct")
        truth = value_truth if basis_truth else False
        note = (
            f"SEC {source_kind} {source_period} reports {_fmt_usd(source_record['value'])}; "
            f"the claim labels it as {quarter_period} and states {_fmt_usd(stated)}."
        )
        return {"truth": bool(truth), "facts": [claimed_record, source_record], "note": note}

    if trap_type in {"fiscal_label_correct", "fiscal_label_as_calendar"}:
        fiscal_period = _period_from_spec({"period": spec.get("fiscal_period") or period})
        fiscal_selected = _select_fact(snapshot, metric, fiscal_period)
        fiscal_record = _fact_record(snapshot, metric, fiscal_period, fiscal_selected, role="fiscal_reference")
        if not _fact_is_present(fiscal_record):
            return {
                "truth": None,
                "facts": [fiscal_record],
                "note": f"SEC snapshot has no {fiscal_period} {ticker} {metric} fact.",
            }
        stated = _stated_base(spec)
        precision = float(spec.get("precision") or 0.0) * _scale_factor(spec)
        value_truth = abs(float(fiscal_record["value"]) - stated) <= precision / 2.0 + 1e-6
        truth = value_truth if trap_type == "fiscal_label_correct" else False
        return {
            "truth": bool(truth),
            "facts": [fiscal_record],
            "note": (
                f"SEC {fiscal_period} reports {_fmt_usd(fiscal_record['value'])}; "
                f"stated {_fmt_usd(stated)} with {trap_type.replace('_', ' ')}."
            ),
        }

    calendar_fact = _select_fact(snapshot, metric, period, basis="calendar")
    fiscal_period_value = spec.get("fiscal_period")
    fiscal_period = (
        _period_from_spec({"period": fiscal_period_value})
        if fiscal_period_value is not None
        else None
    )
    if fiscal_period is not None:
        fiscal_fact = _select_fact(snapshot, metric, fiscal_period)
        fiscal_record = _fact_record(snapshot, metric, fiscal_period, fiscal_fact, role="fiscal_reference")
        calendar_record = _fact_record(snapshot, metric, period, calendar_fact, role="calendar_reference")
        if not _fact_is_present(fiscal_record):
            return {
                "truth": None,
                "facts": [fiscal_record, calendar_record],
                "note": f"SEC snapshot has no {_period_display(fiscal_period)} {ticker} {metric} fact for comparison.",
            }
        if not _fact_is_present(calendar_record):
            return {
                "truth": False,
                "facts": [fiscal_record, calendar_record],
                "note": (
                    f"SEC {_period_display(fiscal_period)} reports {_fmt_usd(fiscal_record['value'])}, "
                    f"but no calendar {period} {ticker} {metric} fact is present."
                ),
            }
        stated = _stated_base(spec)
        precision = float(spec.get("precision") or 0.0) * _scale_factor(spec)
        actual = float(calendar_record["value"])
        truth = abs(actual - stated) <= precision / 2.0 + 1e-6
        fiscal_dates = _date_range(fiscal_record)
        calendar_dates = _date_range(calendar_record)
        fiscal_label = _period_display(fiscal_period)
        calendar_label = f"calendar {period}"
        if fiscal_dates:
            fiscal_label = f"{fiscal_label} ({fiscal_dates})"
        if calendar_dates:
            calendar_label = f"{calendar_label} ({calendar_dates})"
        return {
            "truth": bool(truth),
            "facts": [fiscal_record, calendar_record],
            "note": (
                f"SEC {fiscal_label} reports {_fmt_usd(fiscal_record['value'])}; "
                f"SEC {calendar_label} reports {_fmt_usd(calendar_record['value'])}; "
                f"stated {_fmt_usd(stated)}."
            ),
        }

    sec_fact = _select_fact(snapshot, metric, period, basis="sec")
    record = _fact_record(snapshot, metric, period, sec_fact, role="fiscal_reference")
    if calendar_fact is not None:
        record = _fact_record(snapshot, metric, period, calendar_fact, role="calendar_reference")
    if not _fact_is_present(record):
        return {
            "truth": False,
            "facts": [record],
            "note": f"No calendar {period} {ticker} {metric} fact is present in the SEC snapshot; the stated period is wrong.",
        }
    # A period trap is intentionally false when a fact exists only for the
    # issuer's fiscal quarter rather than the calendar quarter named in the
    # claim.  A calendar match is still checked as an ordinary rounded value.
    if calendar_fact is None:
        fiscal_record = _fact_record(snapshot, metric, period, sec_fact, role="fiscal_reference")
        return {
            "truth": False,
            "facts": [fiscal_record],
            "note": (
                f"SEC fiscal {period} reports {_fmt_usd(fiscal_record['value'])}, but the claim says calendar {period}; "
                f"the period basis is false ({fiscal_record.get('accn') or 'no accession'})."
            ),
        }
    stated = _stated_base(spec)
    precision = float(spec.get("precision") or 0.0) * _scale_factor(spec)
    actual = float(record["value"])
    truth = abs(actual - stated) <= precision / 2.0 + 1e-6
    return {
        "truth": bool(truth),
        "facts": [record],
        "note": f"SEC calendar {period} reports {_fmt_usd(actual)} versus stated {_fmt_usd(stated)} ({record.get('accn') or 'no accession'}).",
    }


def evaluate_spec(spec: Mapping[str, Any], snapshots: Mapping[str, CompanySnapshot]) -> dict[str, Any]:
    kind = str(spec.get("kind") or "")
    if kind == "not_checkable":
        return {
            "truth": None,
            "facts": [],
            "note": f"Not checkable from SEC companyfacts: {spec.get('reason', 'no matching SEC metric')}."
        }
    if kind == "value":
        return _value_part(spec, snapshots)
    if kind == "growth":
        return _growth_part(spec, snapshots)
    if kind == "first_time_above":
        return _first_time_part(spec, snapshots)
    if kind == "ambiguous_period":
        return _ambiguous_period_part(spec, snapshots)
    if kind == "period_trap":
        return _period_trap_part(spec, snapshots)
    if kind == "multi":
        parts = spec.get("parts")
        if not isinstance(parts, list) or not parts:
            raise GoldBuildError("multi spec requires a non-empty parts list")
        evaluated = [evaluate_spec(part, snapshots) for part in parts]
        truths = [part["truth"] for part in evaluated]
        if any(value is False for value in truths):
            truth: bool | None = False
        elif any(value is None for value in truths):
            truth = None
        else:
            truth = True
        return {
            "truth": truth,
            "facts": [fact for part in evaluated for fact in part["facts"]],
            "note": " ".join(str(part["note"]) for part in evaluated),
            "parts": evaluated,
        }
    raise GoldBuildError(f"unsupported spec kind {kind!r}")


def _claim_fact_summary(fact: Mapping[str, Any]) -> str:
    if not fact.get("concept"):
        return "— no matching SEC fact"
    value = fact.get("value")
    period = fact.get("period") or "?"
    dates = f"{fact.get('start') or 'instant'}–{fact.get('end') or '?'}"
    accession = fact.get("accn") or "derived/no accession"
    return f"{fact.get('ticker')} {fact.get('metric')} {period} = {_fmt_usd(value)}; {dates}; {accession}"


def _write_review(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Gold review",
        "",
        "Generated from the raw SEC companyfacts snapshot. Values include the selected period dates and accession where available.",
        "",
        "| ID | Split | Category | Claim | Gold verdict | SEC values with periods and accession |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        facts = row.get("facts", [])
        summary = "<br>".join(_claim_fact_summary(fact) for fact in facts if fact.get("concept")) or "— not checkable with SEC companyfacts"
        claim = str(row.get("claim", "")).replace("|", "\\|")
        lines.append(
            f"| {row['id']} | {row['split']} | {row['category']} | {claim} | {row['gold_verdict']} | {summary} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_dataset(
    claims_path: str | Path = DEFAULT_CLAIMS,
    *,
    cache_dir: str | Path = DEFAULT_CACHE,
    jsonl_path: str | Path = DEFAULT_JSONL,
    facts_path: str | Path = DEFAULT_FACTS,
    review_path: str | Path = DEFAULT_REVIEW,
    strict: bool = True,
) -> dict[str, Any]:
    claims = load_claims(claims_path)
    validate_claims(claims, strict=strict)
    cache = Path(cache_dir)
    ticker_map = _load_ticker_map(cache)
    tickers: set[str] = set()
    for claim in claims:
        claim_spec = claim["spec"]
        specs = (
            claim_spec.get("parts", [])
            if claim_spec.get("kind") == "multi"
            else [claim_spec]
        )
        for part_spec in specs:
            if part_spec.get("ticker"):
                tickers.add(str(part_spec["ticker"]).upper())
    snapshots = {ticker: load_snapshot(cache, ticker, ticker_map) for ticker in sorted(tickers)}

    rows: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    for claim in claims:
        evaluation = evaluate_spec(claim["spec"], snapshots)
        derived_truth = evaluation["truth"]
        derived_verdict = (
            "supported" if derived_truth is True else
            "contradicted" if derived_truth is False else
            "insufficient_evidence"
        )
        if claim["gold_verdict"] != derived_verdict:
            disagreement = {
                "id": claim["id"],
                "hand_written": claim["gold_verdict"],
                "derived": derived_verdict,
                "note": evaluation["note"],
            }
            disagreements.append(disagreement)
            print(
                f"DISAGREEMENT {claim['id']}: hand-written {claim['gold_verdict']} != "
                f"spec-derived {derived_verdict} — {evaluation['note']}",
                file=sys.stderr,
            )
        generated = dict(claim)
        generated["gold_note"] = str(evaluation["note"]).splitlines()[0]
        rows.append(
            {
                "id": claim["id"],
                "split": claim["split"],
                "category": claim["category"],
                "claim": claim["claim"],
                "gold_verdict": derived_verdict,
                "gold_note": generated["gold_note"],
                "spec": claim["spec"],
                "facts": evaluation["facts"],
                "parts": evaluation.get("parts", []),
                "source_files": {
                    ticker: {
                        "path": _display_path(snapshots[ticker].path),
                        "sha256": snapshots[ticker].sha256,
                    }
                    for ticker in sorted(tickers)
                    if any(fact.get("ticker") == ticker for fact in evaluation["facts"])
                },
            }
        )
        claim["gold_note"] = generated["gold_note"]

    jsonl_target = Path(jsonl_path)
    jsonl_target.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_target.open("w", encoding="utf-8") as handle:
        for claim in claims:
            handle.write(json.dumps(claim, ensure_ascii=False, separators=(",", ":")) + "\n")

    facts_target = Path(facts_path)
    facts_target.parent.mkdir(parents=True, exist_ok=True)
    facts_target.write_text(
        json.dumps(
            {
                "claims": rows,
                "source_files": {
                    ticker: {"path": _display_path(snapshots[ticker].path), "sha256": snapshots[ticker].sha256}
                    for ticker in sorted(snapshots)
                },
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_review(Path(review_path), rows)
    return {
        "claim_count": len(claims),
        "disagreements": disagreements,
        "claims_path": str(jsonl_target),
        "facts_path": str(facts_target),
        "review_path": str(review_path),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--claims-out", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--facts-out", type=Path, default=DEFAULT_FACTS)
    parser.add_argument("--review-out", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument(
        "--allow-small",
        action="store_true",
        help="allow a fixture with fewer than 30 claims (useful for offline tests)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = build_dataset(
            args.claims,
            cache_dir=args.cache_dir,
            jsonl_path=args.claims_out,
            facts_path=args.facts_out,
            review_path=args.review_out,
            strict=not args.allow_small,
        )
    except GoldBuildError as exc:
        print(f"gold build failed: {exc}", file=sys.stderr)
        return 2
    print(f"Built {result['claim_count']} claims -> {result['claims_path']}")
    print(f"Wrote gold facts -> {result['facts_path']}")
    print(f"Wrote human review -> {result['review_path']}")
    print(f"Gold disagreements: {len(result['disagreements'])}")
    if result["disagreements"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
