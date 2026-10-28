#!/usr/bin/env python3
"""Deterministically generate the v2 synthetic claim set from cached SEC facts.

This module deliberately imports only the independent reader in
``eval/build_gold.py``.  It never imports the production verifier and never
fetches data.  The generated JSONL is therefore reproducible from the cache,
the seed, and this file.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import math
import random
import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = ROOT / ".cache"
DEFAULT_OUTPUT = ROOT / "eval" / "v2" / "claims-generated.jsonl"
DEFAULT_LOG = ROOT / "eval" / "v2" / "generate.log"
DEFAULT_SEED = 20261027
DEFAULT_TARGET = 260

TARGET_TICKERS = (
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM",
    "V", "WMT", "XOM", "JNJ", "UNH", "NFLX", "ORCL", "ADBE", "COST",
    "NKE", "CSCO", "INTC", "AMD", "CRM", "KO", "PEP",
)
# Kept as a readable inventory of the current cached non-calendar issuers;
# generation itself uses the snapshot-derived ``Choice.non_calendar`` flag so
# an issuer added later is handled automatically.
NON_CALENDAR_TICKERS = {"MSFT", "AAPL", "NVDA", "ORCL", "NKE", "CSCO", "ADBE", "COST", "WMT", "V", "CRM"}
METRICS = (
    "revenue", "net_income", "operating_income", "eps_diluted", "gross_profit",
    "total_assets", "cash", "capex", "rd_expense",
)
FAMILIES = (
    "value", "approx", "inequality", "yoy", "period_trap", "unit_trap",
    "multi_part", "record_first", "not_checkable", "ambiguous_period",
)
UNIT_TRAP_METRICS = {"revenue", "net_income", "operating_income", "cash", "total_assets"}
RECORD_METRICS = {"revenue", "net_income", "operating_income", "gross_profit", "capex", "rd_expense"}
NOT_CHECKABLE_REFERENCE_METRICS = {"revenue", "net_income", "operating_income"}
COMPANY_NAMES = {
    "AAPL": ("Apple",),
    "MSFT": ("Microsoft",),
    "NVDA": ("Nvidia", "NVIDIA"),
    "AMZN": ("Amazon",),
    "GOOGL": ("Alphabet", "Google"),
    "META": ("Meta",),
    "TSLA": ("Tesla",),
    "JPM": ("JPMorgan", "JPMorgan Chase"),
    "V": ("Visa",),
    "WMT": ("Walmart",),
    "XOM": ("Exxon Mobil", "ExxonMobil"),
    "JNJ": ("Johnson & Johnson",),
    "UNH": ("UnitedHealth", "UnitedHealth Group"),
    "NFLX": ("Netflix",),
    "ORCL": ("Oracle",),
    "ADBE": ("Adobe",),
    "COST": ("Costco",),
    "NKE": ("Nike",),
    "CSCO": ("Cisco",),
    "INTC": ("Intel",),
    "AMD": ("AMD",),
    "CRM": ("Salesforce",),
    "KO": ("Coca-Cola", "Coca-Cola Co."),
    "PEP": ("PepsiCo",),
}
METRIC_LABELS = {
    "revenue": "revenue",
    "net_income": "net income",
    "operating_income": "operating income",
    "eps_diluted": "diluted EPS",
    "gross_profit": "gross profit",
    "total_assets": "total assets",
    "cash": "cash and cash equivalents",
    "capex": "capital expenditures",
    "rd_expense": "R&D expense",
}
MONTHS = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}
ORDINALS = {1: "first", 2: "second", 3: "third", 4: "fourth"}


class GenerationError(RuntimeError):
    """Raised when the cached facts cannot satisfy the v2 contract."""


def _load_gold_reader() -> Any:
    path = ROOT / "eval" / "build_gold.py"
    module_name = "market_claim_v2_gold_reader"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise GenerationError(f"unable to load independent gold reader: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class Choice:
    ticker: str
    metric: str
    period: str
    value: float
    record: Mapping[str, Any]
    fiscal: bool
    non_calendar: bool


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(float(value)):
        return None
    return float(value)


def _period_year(period: str) -> int:
    match = re.search(r"(20\d{2})", str(period))
    if not match:
        raise GenerationError(f"invalid period {period!r}")
    return int(match.group(1))


def _period_quarter(period: str) -> int | None:
    match = re.search(r"Q([1-4])", str(period).upper())
    return int(match.group(1)) if match else None


def _is_annual(period: str) -> bool:
    return str(period).upper().startswith("FY") and "Q" not in str(period).upper()


def _period_basis_for_style(choice: Choice, style: int) -> str:
    period = choice.period.upper()
    quarter = _period_quarter(period)
    if quarter is None or _is_annual(period):
        return "fiscal" if choice.fiscal else "calendar"
    if style % 8 in {4, 5} and not choice.non_calendar:
        return "month_named"
    return "fiscal" if choice.fiscal else "calendar"


def _period_text(choice: Choice, style: int) -> str:
    period = choice.period.upper()
    year = _period_year(period)
    quarter = _period_quarter(period)
    end = str(choice.record.get("end") or "")
    end_date = None
    try:
        end_date = date.fromisoformat(end)
    except ValueError:
        pass
    if quarter is None or _is_annual(period):
        if choice.fiscal:
            end_month = MONTHS.get(end_date.month, "the year-end month") if end_date else "the year-end month"
            options = (
                f"fiscal {year}", f"FY{year}", f"the {year} fiscal year",
                f"full-year {year}", f"fiscal year {year}",
                f"the year ended {end_month} {year}", f"fiscal year {year}",
                f"the {year} fiscal year",
            )
        else:
            options = (
                f"calendar {year}", f"calendar year {year}", f"the {year} calendar year",
                f"full calendar year {year}", f"the full year of {year}",
                f"the year ended December {year}", f"calendar-year {year}",
                f"the {year} full calendar year",
            )
        return options[style % len(options)]
    # Name quarters by the month they end in, shifted back a week so 52/53-week quarters that end in the first days
    # of a month keep the conventional name (e.g. a quarter ending 2023-10-01 is "the September 2023 quarter").
    named_end = (end_date - timedelta(days=7)) if end_date else None
    month = f"{MONTHS[named_end.month]} {named_end.year}" if named_end else f"Q{quarter} {year}"
    if choice.fiscal and choice.non_calendar:
        options = (
            f"fiscal Q{quarter} {year}", f"the {ORDINALS[quarter]} quarter of fiscal {year}",
            f"fiscal {ORDINALS[quarter]} quarter {year}", f"the fiscal {ORDINALS[quarter]} quarter of {year}",
            f"fiscal {year} Q{quarter}", f"Q{quarter} of fiscal {year}",
            f"the fiscal Q{quarter} period of {year}", f"the {ORDINALS[quarter]} fiscal quarter of {year}",
        )
        return options[style % len(options)]
    if not choice.fiscal and choice.non_calendar:
        options = (
            f"calendar Q{quarter} {year}", f"the {ORDINALS[quarter]} calendar quarter of {year}",
            f"calendar Q{quarter} {year}", f"the {ORDINALS[quarter]} calendar quarter of {year}",
            f"calendar {year} Q{quarter}", f"Q{quarter} of calendar {year}",
            f"the calendar Q{quarter} period of {year}", f"the {ORDINALS[quarter]} calendar quarter of {year}",
        )
        return options[style % len(options)]
    if not choice.fiscal:
        options = (
            f"Q{quarter} {year}", f"the {ORDINALS[quarter]} quarter of {year}",
            f"calendar Q{quarter} {year}", f"the {ORDINALS[quarter]} calendar quarter of {year}",
            f"the {month} quarter", f"the quarter ended {month}",
            f"the {year} Q{quarter} period", f"the {ORDINALS[quarter]} quarter in {year}",
        )
        return options[style % len(options)]
    options = (
        f"Q{quarter} {year}", f"the {ORDINALS[quarter]} quarter of fiscal {year}",
        f"fiscal Q{quarter} {year}", f"the fiscal {ORDINALS[quarter]} quarter of {year}",
        f"the {month} quarter", f"the quarter ended {month}",
        f"the {year} Q{quarter} period", f"the {ORDINALS[quarter]} fiscal quarter of {year}",
    )
    return options[style % len(options)]


def _company(ticker: str, style: int) -> str:
    return COMPANY_NAMES[ticker][style % len(COMPANY_NAMES[ticker])]


def _metric_label(metric: str) -> str:
    return METRIC_LABELS[metric]


def _naturalize(text: str) -> str:
    """Remove article collisions introduced by composable period templates."""

    return (
        text.replace("The the ", "The ")
        .replace("the the ", "the ")
        .replace("'s the ", "'s ")
    )


def _scale_for(value: float, metric: str) -> tuple[str, float, int]:
    """Return a readable scale, unit step, and decimal count."""

    if metric == "eps_diluted":
        return "usd", 0.01, 2
    magnitude = abs(value)
    if magnitude >= 1_000_000_000:
        return "billion", 0.1, 1
    if magnitude >= 1_000_000:
        return "million", 1.0, 0
    if magnitude >= 1_000:
        return "usd", 1.0, 0
    return "usd", 0.01, 2


def _number(value: float, scale: str, decimals: int, style: int) -> str:
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    if scale == "billion":
        numeric = f"{magnitude:.{decimals}f}"
        options = (f"{sign}${numeric} billion", f"{sign}${numeric}B", f"{sign}${numeric} billion", f"{sign}${numeric}B")
    elif scale == "million":
        numeric = f"{magnitude:,.{decimals}f}"
        options = (f"{sign}${numeric} million", f"{sign}${numeric}M", f"{sign}${numeric} million", f"{sign}${numeric}M")
    else:
        numeric = f"{magnitude:,.{decimals}f}"
        options = (f"{sign}${numeric}", f"{sign}${numeric} USD", f"{sign}${numeric}")
    return options[style % len(options)]


def _safe_rounding(actual: float, scale_value: float, scale: str, step: float, decimals: int) -> tuple[float, float, int]:
    """Choose a rounded stated value away from the half-step ambiguity zone."""

    for candidate_step, candidate_decimals in ((step, decimals), (step * 5, max(0, decimals - 1)), (step * 10, 0)):
        rounded = round(actual / scale_value, candidate_decimals)
        distance = abs(actual - rounded * scale_value)
        if distance < 0.4 * candidate_step * scale_value + 1e-7:
            return rounded, candidate_step, candidate_decimals
    rounded = round(actual / scale_value, decimals)
    return rounded, step, decimals


def _round_spec(actual: float, metric: str) -> tuple[float, str, float, int]:
    scale, step, decimals = _scale_for(actual, metric)
    scale_value = {"usd": 1.0, "million": 1_000_000.0, "billion": 1_000_000_000.0}[scale]
    stated, chosen_step, chosen_decimals = _safe_rounding(actual, scale_value, scale, step, decimals)
    return stated, scale, chosen_step, chosen_decimals


def _scaled_number(actual: float, metric: str, style: int = 0) -> tuple[float, str, float, int, str]:
    stated, scale, precision, decimals = _round_spec(actual, metric)
    return stated, scale, precision, decimals, _number(stated, scale, decimals, style)


def _source_facts(evaluated: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            if value.get("concept") is not None and value.get("value") is not None:
                compact = {
                    "concept": value.get("concept"),
                    "start": value.get("start"),
                    "end": value.get("end"),
                    "accn": value.get("accn"),
                    "form": value.get("form"),
                    "value": value.get("value"),
                    "file_sha256": value.get("source_sha256"),
                }
                key = tuple(compact.get(k) for k in compact)
                if key not in seen:
                    seen.add(key)
                    result.append(compact)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(evaluated.get("facts", []))
    return result


def _split_for(seed: int, family: str, verdict: str, index: int) -> str:
    digest = hashlib.sha256(f"{seed}:{family}:{verdict}:{index}".encode("utf-8")).digest()
    return "dev" if int.from_bytes(digest[:8], "big") % 10 < 3 else "test"


def _truth_verdict(truth: Any) -> str:
    if truth is True:
        return "supported"
    if truth is False:
        return "contradicted"
    return "insufficient_evidence"


def _base_spec(choice: Choice) -> dict[str, Any]:
    return {
        "kind": "value",
        "ticker": choice.ticker,
        "metric": choice.metric,
        "period": choice.period,
        "period_basis": "fiscal" if choice.fiscal else "calendar",
    }


def _choice_from_selected(bg: Any, snap: Any, ticker: str, metric: str, period: str, fiscal: bool) -> Choice | None:
    basis = "fiscal" if fiscal else "calendar"
    selected = bg._select_fact(snap, metric, period, basis=basis)
    record = bg._fact_record(snap, metric, period, selected)
    value = _as_number(record.get("value"))
    if value is None:
        return None
    return Choice(ticker, metric, period, value, record, fiscal, bool(bg.is_non_calendar_issuer(snap)))


def _inventory(bg: Any, cache_dir: Path, logger: logging.Logger) -> tuple[dict[str, Any], dict[str, list[Choice]], list[Choice], list[Choice]]:
    ticker_map = bg._load_ticker_map(cache_dir)
    snapshots: dict[str, Any] = {}
    by_metric: dict[str, list[Choice]] = {metric: [] for metric in METRICS}
    fiscal_choices: list[Choice] = []
    calendar_choices: list[Choice] = []
    for ticker in TARGET_TICKERS:
        try:
            snapshots[ticker] = bg.load_snapshot(cache_dir, ticker, ticker_map)
        except bg.GoldBuildError as exc:
            logger.warning("skip company %s: %s", ticker, exc)
    for ticker in TARGET_TICKERS:
        snap = snapshots.get(ticker)
        if snap is None:
            continue
        for metric in METRICS:
            if metric not in bg.METRIC_ALIASES:
                logger.warning("skip %s/%s: no independent metric alias", ticker, metric)
                continue
            choices: list[Choice] = []
            for year in range(2023, 2027):
                for quarter in range(1, 5):
                    for period, fiscal in ((f"FY{year}Q{quarter}", True), (f"{year}Q{quarter}", False)):
                        try:
                            choice = _choice_from_selected(bg, snap, ticker, metric, period, fiscal)
                        except bg.GoldBuildError:
                            choice = None
                        if choice is not None:
                            choices.append(choice)
                            (fiscal_choices if fiscal else calendar_choices).append(choice)
                try:
                    choice = _choice_from_selected(bg, snap, ticker, metric, f"FY{year}", True)
                except bg.GoldBuildError:
                    choice = None
                if choice is not None:
                    choices.append(choice)
                    fiscal_choices.append(choice)
            # Keep the inventory compact and deterministic while retaining one
            # representative fact for every available period.
            by_metric[metric].extend(choices)
            if not choices:
                logger.info("skip %s/%s: no 2023-2026 fact", ticker, metric)
    return snapshots, by_metric, fiscal_choices, calendar_choices


def _pick(
    pool: Iterable[Choice],
    index: int,
    rng: random.Random,
    *,
    fiscal: bool | None = None,
    ticker: str | None = None,
    metric: str | None = None,
) -> Choice:
    values = [
        item for item in pool
        if (fiscal is None or item.fiscal == fiscal)
        and (ticker is None or item.ticker == ticker)
        and (metric is None or item.metric == metric)
    ]
    if not values:
        values = [item for item in pool if metric is None or item.metric == metric]
    if not values:
        values = list(pool)
    if not values:
        raise GenerationError("fact inventory is empty")
    return values[(index * 37 + rng.randrange(len(values))) % len(values)]


def _special_pools(bg: Any, snapshots: Mapping[str, Any], fiscal_pool: list[Choice]) -> dict[str, list[Choice]]:
    """Build pools whose extra period relationships are known to exist."""

    pools: dict[str, list[Choice]] = {
        "yoy": [], "period_ytd": [], "period_annual": [], "period_fiscal": [],
        "record": [], "ambiguous": [],
    }
    seen: dict[str, set[tuple[str, str, str]]] = {key: set() for key in pools}
    for choice in fiscal_pool:
        ticker = choice.ticker
        snap = snapshots[ticker]
        quarter = _period_quarter(choice.period)
        year = _period_year(choice.period)
        if quarter is not None:
            base_period = f"FY{year - 1}Q{quarter}"
        else:
            base_period = f"FY{year - 1}"
        base = _choice_from_selected(bg, snap, ticker, choice.metric, base_period, True)
        if year >= 2024 and base is not None and base.value != 0:
            actual_pct = (choice.value / base.value - 1.0) * 100.0
            rounded = round(abs(actual_pct))
            if abs(actual_pct) >= 1.0 and abs(abs(actual_pct) - rounded) <= 0.25:
                key = (ticker, choice.metric, choice.period)
                if key not in seen["yoy"]:
                    seen["yoy"].add(key)
                    pools["yoy"].append(choice)
        if quarter == 3:
            ytd = bg._select_fiscal_duration_fact(snap, choice.metric, choice.period, "ytd")
            qtr = bg._select_fiscal_duration_fact(snap, choice.metric, choice.period, "quarter")
            if ytd is not None and qtr is not None:
                key = (ticker, choice.metric, choice.period)
                if key not in seen["period_ytd"]:
                    seen["period_ytd"].add(key)
                    pools["period_ytd"].append(choice)
        if quarter == 4:
            annual = bg._select_fiscal_duration_fact(snap, choice.metric, f"FY{year}", "annual")
            qtr = bg._select_fact(snap, choice.metric, choice.period)
            if annual is not None and qtr is not None:
                key = (ticker, choice.metric, choice.period)
                if key not in seen["period_annual"]:
                    seen["period_annual"].add(key)
                    pools["period_annual"].append(choice)
        if choice.non_calendar and choice.fiscal and quarter is not None:
            fiscal = bg._select_fact(snap, choice.metric, choice.period, basis="fiscal")
            calendar = bg._select_fact(snap, choice.metric, f"{year}Q{quarter}", basis="calendar")
            if fiscal is not None and calendar is not None and _as_number(calendar[2].get("val")) is not None:
                key = (ticker, choice.metric, choice.period)
                if key not in seen["period_fiscal"]:
                    seen["period_fiscal"].add(key)
                    pools["period_fiscal"].append(choice)

                calendar_value = float(calendar[2]["val"])
                if choice.metric in {"revenue", "net_income", "operating_income", "gross_profit"} and abs(choice.value - calendar_value) > max(abs(choice.value), abs(calendar_value), 1.0) * 0.02:
                    if key not in seen["ambiguous"]:
                        seen["ambiguous"].add(key)
                        pools["ambiguous"].append(choice)

        history = bg._all_quarter_records(snap, choice.metric)
        target = bg._fact_record(snap, choice.metric, choice.period, bg._select_fact(snap, choice.metric, choice.period), role="target")
        if not bg._fact_is_present(target):
            continue
        end = bg._as_date(target.get("end"))
        prior = [
            float(item["value"])
            for item in history
            if end is not None
            and bg._as_date(item.get("end")) is not None
            and bg._as_date(item.get("end")) < end
            and _as_number(item.get("value")) is not None
        ]
        if choice.metric in RECORD_METRICS and quarter is not None and prior and float(target["value"]) > max(prior):
            key = (ticker, choice.metric, choice.period)
            if key not in seen["record"]:
                seen["record"].add(key)
                pools["record"].append(choice)
    # Keep the review anchors stable: these are canonical examples where an
    # unqualified quarter is visibly fiscal-vs-calendar (NVIDIA Q2 2024 is
    # roughly $13.5B vs $30.0B; Microsoft Q2 2024 also has two readings).
    anchors: list[Choice] = []
    for anchor_ticker in ("NVDA", "MSFT"):
        anchors.extend(
            item for item in pools["ambiguous"]
            if item.ticker == anchor_ticker
            and item.metric == "revenue"
            and item.period == "FY2024Q2"
        )
    anchor_keys = {(item.ticker, item.metric, item.period) for item in anchors}
    pools["ambiguous"] = anchors + [
        item for item in pools["ambiguous"]
        if (item.ticker, item.metric, item.period) not in anchor_keys
    ]
    return pools


def _value_variant(choice: Choice, variant: str, rng: random.Random, *, force_unit: str | None = None) -> tuple[dict[str, Any], dict[str, Any], str]:
    actual = choice.value
    stated, scale, precision, decimals, _ = _scaled_number(actual, choice.metric, rng.randrange(4))
    if force_unit is not None:
        scale = force_unit
        scale_value = {"usd": 1.0, "million": 1_000_000.0, "billion": 1_000_000_000.0}[scale]
        decimals = 2 if scale == "usd" and abs(actual) < 1000 else (1 if scale == "billion" else 0)
        stated = round(actual / scale_value, decimals)
        precision = 0.01 if scale == "usd" and decimals == 2 else (0.1 if scale == "billion" else 1.0)
    if variant == "contradicted":
        factor = rng.uniform(0.03, 0.15)
        sign = -1.0 if rng.random() < 0.12 and abs(actual) > 0 else 1.0
        false_actual = actual * (1.0 + sign * factor)
        scale_value = {"usd": 1.0, "million": 1_000_000.0, "billion": 1_000_000_000.0}[scale]
        stated = round(false_actual / scale_value, decimals)
        for _ in range(8):
            if abs(actual - stated * scale_value) > 0.6 * precision * scale_value + 1e-6:
                break
            factor = min(0.35, factor + 0.04)
            false_actual = actual * (1.0 + sign * factor)
            stated = round(false_actual / scale_value, decimals)
        perturbation = {"kind": "value_error", "factor": round(false_actual / actual - 1.0, 6) if actual else None}
    else:
        perturbation = {"kind": "rounded_value", "factor": 0.0}
    spec = _base_spec(choice)
    spec.update({"stated": stated, "scale": scale, "precision": precision, "comparator": "eq"})
    label = _number(stated, scale, decimals, rng.randrange(4))
    return spec, perturbation, label


VALUE_TEMPLATES = (
    "{company} reported {metric} of {number} in {period}.",
    "In {period}, {company}'s {metric} came in at {number}.",
    "{company}'s {period} {metric} totaled {number}.",
    "The {period} filing puts {company}'s {metric} at {number}.",
    "For {period}, {company} posted {number} of {metric}.",
    "{company} disclosed {number} in {metric} for {period}.",
    "The {period} {metric} figure for {company} was {number}.",
    "{company} said its {metric} reached {number} during {period}.",
)
APPROX_TEMPLATES = (
    "{company}'s {metric} was about {number} in {period}.",
    "In {period}, {company} recorded roughly {number} of {metric}.",
    "{company} came in at approximately {number} for {period} {metric}.",
    "The {period} {metric} result was around {number} at {company}.",
    "About {number} was reported as {company}'s {metric} in {period}.",
    "{company}'s {period} filing showed close to {number} in {metric}.",
    "Roughly {number} of {metric} was posted by {company} for {period}.",
    "The {period} number for {company}'s {metric} was near {number}.",
)
INEQUALITY_TEMPLATES = (
    "{company}'s {metric} topped {number} in {period}.",
    "In {period}, {company} was below {number} on {metric}.",
    "{company} reported at least {number} of {metric} for {period}.",
    "The {period} {metric} figure at {company} was above {number}.",
    "{company}'s {metric} stayed under {number} during {period}.",
    "For {period}, {company} cleared the {number} mark in {metric}.",
    "{company} had no less than {number} of {metric} in {period}.",
    "The {period} filing says {company}'s {metric} was less than {number}.",
)
YOY_TEMPLATES = (
    "{company}'s {metric} rose {pct}% year over year in {period}.",
    "In {period}, {company} saw {metric} increase {pct}% from a year earlier.",
    "{company} said {metric} was up {pct}% YoY for {period}.",
    "The {period} {metric} result fell {pct}% year over year at {company}.",
    "{company}'s {metric} decreased {pct}% from the prior year in {period}.",
    "Year over year, {metric} at {company} moved {direction} {pct}% in {period}.",
    "The {period} filing showed {metric} {direction} {pct}% for {company}.",
    "{company} posted a {pct}% year-over-year {direction_word} in {metric} during {period}.",
)
PERIOD_TEMPLATES = (
    "{company}'s {metric} was {number} in {period_phrase}.",
    "The {period_phrase} {metric} figure for {company} was {number}.",
    "{company} reported {number} of {metric} for {period_phrase}.",
    "In {period_phrase}, {company} posted {number} of {metric}.",
    "{company}'s filing lists {number} for {metric} in {period_phrase}.",
    "The {metric} total reached {number} at {company} in {period_phrase}.",
    "For {period_phrase}, {company} disclosed {number} in {metric}.",
    "{company} said {metric} was {number} during {period_phrase}.",
)
UNIT_TEMPLATES = (
    "{company}'s {period} {metric} was {number}.",
    "In {period}, {company} reported {number} of {metric}.",
    "The {period} filing puts {company}'s {metric} at {number}.",
    "{company} posted {number} in {metric} for {period}.",
    "{metric} at {company} came to {number} in {period}.",
    "For {period}, the {metric} figure was {number} at {company}.",
    "{company}'s disclosed {metric} totaled {number} during {period}.",
    "The {period} {metric} amount for {company} was {number}.",
)
MULTI_TEMPLATES = (
    "In {period1}, {company1} reported {metric1} of {number1} and {metric2} of {number2}.",
    "{company1}'s {period1} filing showed {number1} in {metric1}, plus {number2} in {metric2}.",
    "For {period1}, {company1} posted {number1} of {metric1} alongside {number2} of {metric2}.",
    "The {period1} results: {company1} had {metric1} at {number1} and {metric2} at {number2}.",
    "{company1} disclosed {number1} in {metric1} and {number2} in {metric2} for {period1}.",
    "During {period1}, {company1}'s {metric1} reached {number1}; {metric2} was {number2}.",
    "{company1}'s {period1} report put {metric1} at {number1}, with {metric2} of {number2}.",
    "The {period1} filing says {company1} recorded {number1} in {metric1} and {number2} in {metric2}.",
)
RECORD_TEMPLATES = (
    "{company}'s {period} {metric} topped {number} for the first time.",
    "During {period}, {company} posted a record {metric} of {number}.",
    "{company}'s {period} {metric} was its highest ever, at {number}.",
    "{company} set a record with {number} in {metric} during {period}.",
    "At {number}, {company}'s {metric} in {period} was a record.",
    "{company} posted its highest-ever {metric}—{number}—in {period}.",
    "For {metric}, {company} topped {number} for the first time in {period}.",
    "The {period} filing marked a record {metric} of {number} for {company}.",
)
NOT_CHECKABLE_TEMPLATES = (
    "{company}'s {period} guidance calls for {number} of revenue.",
    "Analysts expect {company}'s share price to reach {number} next year.",
    "{company} held {number}% of the global market in {period}.",
    "{company}'s next fiscal year revenue will reach {number}.",
    "Management forecast {company}'s adjusted earnings at {number} next quarter.",
    "{company}'s cloud segment is expected to deliver {number} in {period}.",
    "Analysts say {company} will reach {number} next year.",
    "{company}'s upcoming guidance projects adjusted operating income of {number}.",
)
AMBIGUOUS_TEMPLATES = (
    "{company}'s Q{quarter} {year} {metric} was {number}.",
    "In the {ordinal} quarter of {year}, {company} reported {number} of {metric}.",
    "{company}'s {year} Q{quarter} period {metric} came in at {number}.",
    "For Q{quarter} {year}, {company} posted {number} in {metric}.",
    "The {ordinal} quarter of {year} put {company}'s {metric} at {number}.",
    "{company} disclosed {number} of {metric} during its Q{quarter} {year} period.",
    "The {year} Q{quarter} filing showed {company}'s {metric} at {number}.",
    "{company}'s {metric} reached {number} in the Q{quarter} {year} quarter.",
)


AMBIGUOUS_GTE_TEMPLATES = (
    "{company}'s {metric} was at least {number} in Q{quarter} {year}.",
    "{company} reported no less than {number} of {metric} for Q{quarter} {year}.",
    "In Q{quarter} {year}, {company}'s {metric} came in at {number} or more.",
    "{company}'s Q{quarter} {year} {metric} was at least {number}.",
)


def _ambiguous_period_text(choice: Choice, style: int) -> str:
    quarter = _period_quarter(choice.period)
    if quarter is None:
        raise GenerationError("ambiguous_period requires a quarter")
    year = _period_year(choice.period)
    return (
        f"Q{quarter} {year}", f"the {ORDINALS[quarter]} quarter of {year}",
        f"the {year} Q{quarter} period", f"Q{quarter} {year}",
        f"the {ORDINALS[quarter]} quarter of {year}", f"Q{quarter} {year}",
        f"the {year} Q{quarter} filing", f"Q{quarter} {year} quarter",
    )[style % 8]


def _reference_choice_for_not_checkable(
    bg: Any,
    snapshots: Mapping[str, Any],
    choice: Choice,
    preferred_metrics: Iterable[str] = ("revenue", "net_income", "operating_income"),
) -> Choice:
    for metric in preferred_metrics:
        try:
            candidate = _choice_from_selected(
                bg, snapshots[choice.ticker], choice.ticker, metric, choice.period, choice.fiscal
            )
        except bg.GoldBuildError:
            candidate = None
        if candidate is not None and abs(candidate.value) >= 1_000_000:
            return candidate
    return choice


def _not_checkable_numbers(bg: Any, snapshots: Mapping[str, Any], choice: Choice, index: int) -> dict[str, str]:
    revenue_reference = _reference_choice_for_not_checkable(
        bg, snapshots, choice, ("revenue", "net_income", "operating_income")
    )
    income_reference = _reference_choice_for_not_checkable(
        bg, snapshots, choice, ("net_income", "operating_income", "revenue")
    )
    revenue_base = max(abs(revenue_reference.value), 1_000_000.0)
    income_base = max(abs(income_reference.value), 1_000_000.0)
    financial_actual = revenue_base * (0.90 + (index % 5) * 0.05)
    adjusted_actual = income_base * (1.05 + (index % 4) * 0.05)
    segment_actual = revenue_base * (0.08 + (index % 4) * 0.03)
    financial = _scaled_number(financial_actual, "revenue", index)[4]
    adjusted = _scaled_number(adjusted_actual, "revenue", index + 1)[4]
    segment = _scaled_number(segment_actual, "revenue", index + 2)[4]
    share_price = f"${max(10.0, min(1_000.0, 60.0 * math.sqrt(revenue_base / 1_000_000_000.0)) + (index % 7) * 3.0):.2f}"
    market_share = f"{5 + (index * 7) % 26}"
    operational_count = max(1, round(revenue_base / 1_000_000_000.0 * (1 + index % 3)))
    if choice.ticker == "TSLA":
        operational = f"{max(1, min(5, operational_count)):,} million vehicle deliveries"
    elif choice.ticker == "NFLX":
        operational = f"{max(1, min(400, operational_count)):,} million subscribers"
    elif choice.ticker == "COST":
        operational = f"{max(1, min(200, operational_count)):,} million members"
    else:
        operational = f"{max(1, min(75, operational_count)):,} million customers"
    return {
        "financial": financial,
        "adjusted": adjusted,
        "segment": segment,
        "share_price": share_price,
        "market_share": market_share,
        "operational": operational,
    }


def _make_claim(
    bg: Any,
    snapshots: Mapping[str, Any],
    family: str,
    variant: str,
    index: int,
    choice: Choice,
    rng: random.Random,
) -> dict[str, Any]:
    company = _company(choice.ticker, rng.randrange(8))
    metric = _metric_label(choice.metric)
    period_style = rng.randrange(8)
    period = _period_text(choice, period_style)
    period_basis = _period_basis_for_style(choice, period_style)
    perturbation: dict[str, Any]
    spec: dict[str, Any]
    claim: str

    if family == "value":
        spec, perturbation, number = _value_variant(choice, variant, rng)
        claim = VALUE_TEMPLATES[index % len(VALUE_TEMPLATES)].format(company=company, metric=metric, period=period, number=number)
    elif family == "approx":
        actual = choice.value
        stated, scale, _, decimals, number = _scaled_number(actual, choice.metric, rng.randrange(4))
        tolerance = 5.0
        if variant == "contradicted":
            factor = rng.uniform(0.08, 0.15)
            stated = round((actual * (1.0 + factor)) / {"usd": 1.0, "million": 1_000_000.0, "billion": 1_000_000_000.0}[scale], decimals)
            perturbation = {"kind": "approx_value_error", "factor": round(factor, 6)}
        else:
            perturbation = {"kind": "approximate_value", "factor": 0.0}
        spec = _base_spec(choice)
        spec.update({"stated": stated, "scale": scale, "tolerance_pct": tolerance, "comparator": "approx"})
        claim = APPROX_TEMPLATES[index % len(APPROX_TEMPLATES)].format(company=company, metric=metric, period=period, number=_number(stated, scale, decimals, index))
    elif family == "inequality":
        comparator_by_template = ("gt", "lt", "gte", "gt", "lt", "gt", "gte", "lt")
        comparator = comparator_by_template[index % len(comparator_by_template)]
        magnitude = max(abs(choice.value) * 0.12, 1.0 if choice.metric == "eps_diluted" else 1_000_000.0)
        if comparator in {"gt", "gte"}:
            threshold = choice.value - magnitude if variant == "supported" else choice.value + magnitude
        else:
            threshold = choice.value + magnitude if variant == "supported" else choice.value - magnitude
        scale, step, decimals = _scale_for(threshold, choice.metric)
        scale_value = {"usd": 1.0, "million": 1_000_000.0, "billion": 1_000_000_000.0}[scale]
        stated = round(threshold / scale_value, decimals)
        spec = _base_spec(choice)
        spec.update({"stated": stated, "scale": scale, "precision": step, "comparator": comparator})
        perturbation = {"kind": "inequality_threshold", "comparator": comparator, "direction": variant}
        claim = INEQUALITY_TEMPLATES[index % len(INEQUALITY_TEMPLATES)].format(company=company, metric=metric, period=period, number=_number(stated, scale, decimals, index))
    elif family == "yoy":
        base_period = f"{_period_year(choice.period) - 1}Q{_period_quarter(choice.period) or 4}" if not _is_annual(choice.period) else f"FY{_period_year(choice.period) - 1}"
        base_choice = _choice_from_selected(bg, snapshots[choice.ticker], choice.ticker, choice.metric, base_period, choice.fiscal)
        if base_choice is None or base_choice.value == 0:
            raise GenerationError(f"missing YoY base for {choice.ticker} {choice.metric} {choice.period}")
        actual_pct = (choice.value / base_choice.value - 1.0) * 100.0
        if abs(actual_pct) < 1.0:
            raise GenerationError("near-zero YoY change is too ambiguous")
        direction = "up" if actual_pct > 0 else "down"
        stated_abs = round(abs(actual_pct))
        if abs(abs(actual_pct) - stated_abs) > 0.25:
            raise GenerationError("YoY claim is near a rounded-percent boundary")
        if variant == "contradicted":
            wrong_direction = "down" if direction == "up" else "up"
            direction = wrong_direction
            perturbation = {"kind": "wrong_direction", "actual_pct": round(actual_pct, 4)}
        else:
            perturbation = {"kind": "rounded_growth", "actual_pct": round(actual_pct, 4)}
        spec = {
            "kind": "growth", "ticker": choice.ticker, "metric": choice.metric,
            "period": choice.period, "base_period": base_period, "stated": stated_abs,
            "direction": direction, "precision": 1.0,
        }
        direction_word = "increase" if direction == "up" else "decline"
        allowed_templates = (0, 1, 2, 5, 6, 7) if direction == "up" else (3, 4, 5, 6, 7)
        template = YOY_TEMPLATES[allowed_templates[index % len(allowed_templates)]]
        claim = template.format(
            company=company, metric=metric, period=period, pct=stated_abs,
            direction=direction, direction_word=direction_word,
        )
    elif family == "period_trap":
        # Prefer Q3 because the SEC exposes a reliable nine-month YTD fact.
        trap = index % 3
        if trap == 0:
            qperiod = f"FY{_period_year(choice.period)}Q3"
            ytd = bg._select_fiscal_duration_fact(snapshots[choice.ticker], choice.metric, qperiod, "ytd")
            quarter = bg._select_fiscal_duration_fact(snapshots[choice.ticker], choice.metric, qperiod, "quarter")
            if ytd is None or quarter is None:
                raise GenerationError("missing quarter/YTD pair")
            ytd_record = bg._fact_record(snapshots[choice.ticker], choice.metric, qperiod, ytd)
            ytd_value = float(ytd_record["value"])
            stated, scale, precision, decimals, _ = _scaled_number(ytd_value, choice.metric, index)
            trap_type = "ytd_correct" if variant == "supported" else "ytd_as_quarter"
            spec = {"kind": "period_trap", "trap_type": trap_type, "ticker": choice.ticker, "metric": choice.metric, "quarter_period": qperiod, "period": qperiod, "period_basis": "fiscal", "stated": stated, "scale": scale, "precision": precision}
            ytd_choice = Choice(choice.ticker, choice.metric, qperiod, ytd_value, ytd_record, True, choice.non_calendar)
            period_phrase = _period_text(ytd_choice, index)
            if variant == "supported":
                period_phrase = (
                    f"the first nine months of fiscal {_period_year(qperiod)}"
                    if choice.non_calendar
                    else f"the first nine months of {_period_year(qperiod)}"
                )
            else:
                period_phrase = f"fiscal Q3 {_period_year(qperiod)}" if choice.non_calendar else f"Q3 {_period_year(qperiod)}"
            claim = PERIOD_TEMPLATES[index % len(PERIOD_TEMPLATES)].format(company=company, metric=metric, period_phrase=period_phrase, number=_number(stated, scale, decimals, index))
            perturbation = {"kind": "period_basis", "basis": "ytd", "label": trap_type}
        elif trap == 1:
            qperiod = f"FY{_period_year(choice.period)}Q4"
            annual_period = f"FY{_period_year(choice.period)}"
            annual = bg._select_fiscal_duration_fact(snapshots[choice.ticker], choice.metric, annual_period, "annual")
            quarter = bg._select_fact(snapshots[choice.ticker], choice.metric, qperiod)
            if annual is None or quarter is None:
                raise GenerationError("missing annual/Q4 pair")
            annual_record = bg._fact_record(snapshots[choice.ticker], choice.metric, annual_period, annual)
            annual_value = float(annual_record["value"])
            stated, scale, precision, decimals, _ = _scaled_number(annual_value, choice.metric, index)
            trap_type = "annual_correct" if variant == "supported" else "annual_as_quarter"
            spec = {"kind": "period_trap", "trap_type": trap_type, "ticker": choice.ticker, "metric": choice.metric, "quarter_period": qperiod, "annual_period": annual_period, "period": qperiod, "period_basis": "fiscal", "stated": stated, "scale": scale, "precision": precision}
            period_phrase = f"fiscal {_period_year(annual_period)}" if variant == "supported" else (f"fiscal Q4 {_period_year(qperiod)}" if choice.non_calendar else f"Q4 {_period_year(qperiod)}")
            claim = PERIOD_TEMPLATES[index % len(PERIOD_TEMPLATES)].format(company=company, metric=metric, period_phrase=period_phrase, number=_number(stated, scale, decimals, index))
            perturbation = {"kind": "period_basis", "basis": "annual", "label": trap_type}
        else:
            if not choice.non_calendar:
                raise GenerationError("fiscal-label trap requires a non-calendar issuer")
            fiscal_period = choice.period if choice.fiscal and _period_quarter(choice.period) else f"FY{_period_year(choice.period)}Q3"
            fiscal = bg._select_fact(snapshots[choice.ticker], choice.metric, fiscal_period)
            calendar_period = f"{_period_year(fiscal_period)}Q{_period_quarter(fiscal_period) or 3}"
            calendar = bg._select_fact(snapshots[choice.ticker], choice.metric, calendar_period, basis="calendar")
            if fiscal is None or calendar is None:
                raise GenerationError("missing fiscal/calendar pair")
            fiscal_record = bg._fact_record(snapshots[choice.ticker], choice.metric, fiscal_period, fiscal)
            fiscal_value = float(fiscal_record["value"])
            stated, scale, precision, decimals, _ = _scaled_number(fiscal_value, choice.metric, index)
            trap_type = "fiscal_label_correct" if variant == "supported" else "fiscal_label_as_calendar"
            fiscal_choice = Choice(choice.ticker, choice.metric, fiscal_period, fiscal_value, fiscal_record, True, choice.non_calendar)
            supported_basis = _period_basis_for_style(fiscal_choice, index)
            spec = {"kind": "period_trap", "trap_type": trap_type, "ticker": choice.ticker, "metric": choice.metric, "period": fiscal_period, "fiscal_period": fiscal_period, "period_basis": supported_basis if variant == "supported" else "calendar", "stated": stated, "scale": scale, "precision": precision}
            period_phrase = _period_text(fiscal_choice, index) if variant == "supported" else f"calendar Q{_period_quarter(fiscal_period) or 3} {_period_year(fiscal_period)}"
            claim = PERIOD_TEMPLATES[index % len(PERIOD_TEMPLATES)].format(company=company, metric=metric, period_phrase=period_phrase, number=_number(stated, scale, decimals, index))
            perturbation = {"kind": "period_label", "label": trap_type, "issuer_fiscal": True}
    elif family == "unit_trap":
        if choice.metric not in UNIT_TRAP_METRICS:
            raise GenerationError(f"unit_trap metric {choice.metric} is not a financial scale metric")
        correct_stated, correct_scale, precision, decimals, _ = _scaled_number(choice.value, choice.metric, index)
        if variant == "supported":
            scale, stated = correct_scale, correct_stated
            perturbation = {"kind": "unit_correct", "scale": scale}
        else:
            scale = "million" if correct_scale == "billion" else "billion" if correct_scale == "million" else "million"
            # Keep the numeric phrase from the correct unit and swap only the
            # label.  For example, $77.7 billion becomes $77.7 million.
            # Interpreting that phrase in the claimed unit is unambiguously
            # false, while remaining a realistic newsroom unit slip.
            stated = correct_stated
            perturbation = {"kind": "unit_swap", "correct_scale": correct_scale, "claimed_scale": scale}
        spec = _base_spec(choice)
        spec.update({"stated": stated, "scale": scale, "precision": precision, "comparator": "eq"})
        claim = UNIT_TEMPLATES[index % len(UNIT_TEMPLATES)].format(company=company, metric=metric, period=period, number=_number(stated, scale, decimals, index))
    elif family == "multi_part":
        # Use a deterministic second fact from a different metric for the same issuer.
        candidate_metrics = [m for m in METRICS if m != choice.metric and m in bg.METRIC_ALIASES]
        second_choice = None
        for metric_name in candidate_metrics:
            try:
                second_choice = _choice_from_selected(bg, snapshots[choice.ticker], choice.ticker, metric_name, choice.period, choice.fiscal)
            except bg.GoldBuildError:
                second_choice = None
            if second_choice is not None:
                break
        if second_choice is None:
            raise GenerationError("missing second fact for multi-part claim")
        spec1, perturbation1, number1 = _value_variant(choice, "supported", rng)
        spec2, perturbation2, number2 = _value_variant(second_choice, variant, rng)
        spec = {"kind": "multi", "parts": [spec1, spec2]}
        perturbation = {"kind": "multi_part", "parts": [perturbation1, perturbation2]}
        claim = MULTI_TEMPLATES[index % len(MULTI_TEMPLATES)].format(
            company1=company, period1=period, metric1=metric, number1=number1,
            metric2=_metric_label(second_choice.metric), number2=number2,
        )
    elif family == "record_first":
        if choice.metric not in RECORD_METRICS or _period_quarter(choice.period) is None:
            raise GenerationError("record_first requires a quarterly flow metric")
        history = bg._all_quarter_records(snapshots[choice.ticker], choice.metric)
        candidates = [item for item in history if _as_number(item.get("value")) is not None]
        if len(candidates) < 3:
            raise GenerationError("not enough history for first-time claim")
        target_selected = bg._select_fact(snapshots[choice.ticker], choice.metric, choice.period, basis="fiscal")
        target = bg._fact_record(snapshots[choice.ticker], choice.metric, choice.period, target_selected, role="target")
        if not bg._fact_is_present(target):
            raise GenerationError("record target is not directly selectable")
        target_value = float(target["value"])
        target_end = bg._as_date(target.get("end"))
        prior = [
            float(item["value"])
            for item in candidates
            if target_end is not None
            and bg._as_date(item.get("end")) is not None
            and bg._as_date(item.get("end")) < target_end
        ]
        prior_high = max(prior) if prior else target_value * 0.5
        if variant == "supported" and target_value <= prior_high:
            raise GenerationError("latest fact is not a first-time high")
        if variant == "supported":
            threshold = (target_value + prior_high) / 2.0
            perturbation = {"kind": "first_time_threshold", "prior_high": prior_high}
        else:
            threshold = target_value * (1.08 if target_value >= 0 else 0.92)
            perturbation = {"kind": "not_first_time", "prior_high": prior_high}
        scale, step, decimals = _scale_for(threshold, choice.metric)
        scale_value = {"usd": 1.0, "million": 1_000_000.0, "billion": 1_000_000_000.0}[scale]
        if variant == "supported":
            # A rounded threshold must remain strictly above the historical
            # high.  A 4M gap cannot be represented by a 0.1B threshold, so
            # step down to millions when the default billion scale is too
            # coarse.
            threshold_options = (
                (("billion", 1), ("million", 0), ("usd", 0))
                if abs(threshold) >= 1_000_000_000
                else (("million", 0), ("usd", 0))
            )
            found_threshold = None
            for candidate_scale, candidate_decimals in threshold_options:
                candidate_value = {"usd": 1.0, "million": 1_000_000.0, "billion": 1_000_000_000.0}[candidate_scale]
                multiplier = 10 ** candidate_decimals
                candidate_stated = math.floor(prior_high / candidate_value * multiplier + 1e-9) / multiplier
                candidate_stated += 1.0 / multiplier
                if candidate_stated * candidate_value < target_value - 1e-6:
                    found_threshold = (candidate_scale, candidate_stated, candidate_value, candidate_decimals)
                    break
            if found_threshold is None:
                raise GenerationError("no rounded threshold between target and prior high")
            scale, threshold_stated, scale_value, decimals = found_threshold
        else:
            threshold_stated = round(threshold / scale_value, decimals)
        spec = {"kind": "first_time_above", "ticker": choice.ticker, "metric": choice.metric, "period": choice.period, "period_basis": _period_basis_for_style(choice, index), "threshold": threshold_stated, "scale": scale}
        target_choice = Choice(choice.ticker, choice.metric, choice.period, target_value, target, choice.fiscal, choice.non_calendar)
        target_period = _period_text(target_choice, index)
        claim = RECORD_TEMPLATES[index % len(RECORD_TEMPLATES)].format(company=company, metric=metric, period=target_period, number=_number(threshold_stated, scale, decimals, index))
    elif family == "not_checkable":
        numbers = _not_checkable_numbers(bg, snapshots, choice, index)
        reason_options = ("guidance", "share price", "market share", "future period", "non-GAAP", "segment result", "operational KPI", "guidance")
        reason = reason_options[index % len(reason_options)]
        spec = {"kind": "not_checkable", "reason": reason, "ticker": choice.ticker, "period_basis": period_basis, "reference_metric": _reference_choice_for_not_checkable(bg, snapshots, choice).metric}
        perturbation = {"kind": "insufficient_evidence", "reason": reason}
        template_index = index % len(NOT_CHECKABLE_TEMPLATES)
        number = (
            numbers["financial"] if template_index in {0, 3}
            else numbers["share_price"] if template_index == 1
            else numbers["market_share"] if template_index == 2
            else numbers["adjusted"] if template_index == 4
            else numbers["segment"] if template_index == 5
            else numbers["operational"] if template_index == 6
            else numbers["adjusted"]
        )
        claim = NOT_CHECKABLE_TEMPLATES[template_index].format(company=company, metric=metric, period=period, number=number)
    elif family == "ambiguous_period":
        if not choice.non_calendar or not choice.fiscal or _period_quarter(choice.period) is None:
            raise GenerationError("ambiguous_period requires a non-calendar fiscal quarter")
        year = _period_year(choice.period)
        quarter = _period_quarter(choice.period)
        calendar_choice = _choice_from_selected(
            bg, snapshots[choice.ticker], choice.ticker, choice.metric, f"{year}Q{quarter}", False
        )
        if calendar_choice is None or choice.value <= 0 or calendar_choice.value <= 0:
            raise GenerationError("ambiguous_period requires two positive readings")
        fiscal_actual = choice.value
        calendar_actual = calendar_choice.value
        mode = "insufficient" if index < 2 or index % 3 == 2 else "supported" if index % 3 == 0 else "contradicted"
        if mode == "supported":
            threshold_actual = min(fiscal_actual, calendar_actual) * 0.85
            comparator = "gte"
            scale, precision, decimals = _scale_for(threshold_actual, choice.metric)
            scale_value = {"usd": 1.0, "million": 1_000_000.0, "billion": 1_000_000_000.0}[scale]
            stated = round(threshold_actual / scale_value, decimals)
            perturbation = {"kind": "same_verdict_both_readings", "reading": "supported"}
        elif mode == "contradicted":
            threshold_actual = max(fiscal_actual, calendar_actual) * 1.15
            comparator = "gte"
            scale, precision, decimals = _scale_for(threshold_actual, choice.metric)
            scale_value = {"usd": 1.0, "million": 1_000_000.0, "billion": 1_000_000_000.0}[scale]
            stated = round(threshold_actual / scale_value, decimals)
            perturbation = {"kind": "same_verdict_both_readings", "reading": "contradicted"}
        else:
            stated, scale, precision, decimals, _ = _scaled_number(fiscal_actual, choice.metric, index)
            comparator = "eq"
            perturbation = {
                "kind": "different_period_readings",
                "fiscal_value": fiscal_actual,
                "calendar_value": calendar_actual,
            }
        period_phrase = _ambiguous_period_text(choice, index)
        spec = {
            "kind": "ambiguous_period", "ticker": choice.ticker, "metric": choice.metric,
            "period": choice.period, "period_basis": "fiscal", "fiscal_period": choice.period,
            "calendar_period": f"{year}Q{quarter}", "stated": stated, "scale": scale,
            "precision": precision, "comparator": comparator,
        }
        templates = AMBIGUOUS_GTE_TEMPLATES if comparator == "gte" else AMBIGUOUS_TEMPLATES
        claim = templates[index % len(templates)].format(
            company=company, metric=metric, number=_number(stated, scale, decimals, index),
            quarter=quarter, year=year, ordinal=ORDINALS[quarter],
        )
    else:
        raise GenerationError(f"unknown family {family}")

    if family in {"value", "approx", "inequality", "yoy", "unit_trap"}:
        spec["period_basis"] = period_basis
    elif family == "multi_part":
        spec["period_basis"] = period_basis
        for part in spec.get("parts", []):
            if isinstance(part, dict):
                part["period_basis"] = period_basis

    claim = _naturalize(claim)
    evaluated = bg.evaluate_spec(spec, snapshots)
    verdict = _truth_verdict(evaluated.get("truth"))
    expected = "supported" if variant == "supported" else "contradicted"
    if family == "not_checkable":
        expected = "insufficient_evidence"
    elif family == "ambiguous_period":
        expected = verdict
    if verdict != expected:
        raise GenerationError(f"self-check mismatch for {family}/{variant}: expected {expected}, got {verdict}; {spec}")
    return {
        "split": _split_for(DEFAULT_SEED, family, verdict, index),
        "category": family,
        "family": family,
        "claim": claim,
        "spec": spec,
        "gold_verdict": verdict,
        "gold_note": str(evaluated.get("note") or "").replace("\n", " "),
        "perturbation": perturbation,
        "source_facts": _source_facts(evaluated),
    }


def generate_claims(
    *,
    seed: int = DEFAULT_SEED,
    target: int = DEFAULT_TARGET,
    cache_dir: str | Path = DEFAULT_CACHE,
    output: str | Path = DEFAULT_OUTPUT,
    log_path: str | Path = DEFAULT_LOG,
) -> list[dict[str, Any]]:
    """Generate and write the deterministic v2 synthetic dataset."""

    if target < len(FAMILIES) * 12:
        raise GenerationError("target must leave at least 12 claims for every family")
    logger = logging.getLogger("market_claim_v2.generate")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler(sys.stderr))
    rng = random.Random(seed)
    bg = _load_gold_reader()
    snapshots, by_metric, fiscal_pool, calendar_pool = _inventory(bg, Path(cache_dir), logger)
    if len(snapshots) < 20:
        raise GenerationError(f"expected at least 20 cached companies, found {len(snapshots)}")
    special = _special_pools(bg, snapshots, fiscal_pool)
    logger.info("special pools: yoy=%d ytd=%d annual=%d fiscal-label=%d record=%d ambiguous=%d", len(special["yoy"]), len(special["period_ytd"]), len(special["period_annual"]), len(special["period_fiscal"]), len(special["record"]), len(special["ambiguous"]))
    unit_pool = [item for item in fiscal_pool if item.metric in UNIT_TRAP_METRICS]
    not_checkable_pool = [item for item in fiscal_pool if item.metric in NOT_CHECKABLE_REFERENCE_METRICS]
    per_family = target // len(FAMILIES)
    remainder = target % len(FAMILIES)
    rows: list[dict[str, Any]] = []
    generated_index = 0
    for family_index, family in enumerate(FAMILIES):
        count = per_family + (1 if family_index < remainder else 0)
        for index in range(count):
            if family == "not_checkable":
                variant = "insufficient_evidence"
            else:
                # Four odd-sized families start with each verdict so the
                # global supported/contradicted counts remain balanced while
                # every family stays stratified.
                starts_supported = family_index < 4
                variant = (
                    "supported"
                    if ((index % 2 == 0) == starts_supported)
                    else "contradicted"
                )
            local_rng = random.Random(rng.randrange(2**63))
            try:
                if family == "not_checkable":
                    choice = _pick(not_checkable_pool or fiscal_pool or calendar_pool, index + family_index * 11, local_rng, fiscal=True)
                elif family == "period_trap":
                    trap_pools = (special["period_ytd"], special["period_annual"], special["period_fiscal"])
                    preferred = trap_pools[index % 3]
                    choice = _pick(preferred, index + family_index * 11, local_rng, fiscal=True)
                elif family == "yoy":
                    choice = _pick(special["yoy"], index + family_index * 11, local_rng, fiscal=True)
                elif family == "record_first":
                    choice = _pick(special["record"], index + family_index * 11, local_rng, fiscal=True)
                elif family == "unit_trap":
                    choice = _pick(unit_pool, index + family_index * 11, local_rng, fiscal=True)
                elif family == "multi_part":
                    choice = _pick(fiscal_pool, index + family_index * 11, local_rng, fiscal=True)
                elif family == "ambiguous_period":
                    if len(special["ambiguous"]) < 12:
                        raise GenerationError("ambiguous_period pool has fewer than 12 items")
                    choice = special["ambiguous"][index % len(special["ambiguous"])]
                else:
                    choice = _pick(fiscal_pool + calendar_pool, index + family_index * 11, local_rng)
                row = _make_claim(bg, snapshots, family, variant, index, choice, local_rng)
            except GenerationError as exc:
                logger.warning("skip %s %s/%s: %s", family, variant, index, exc)
                # Retry from a different deterministic fact.  A fixed retry
                # bound keeps a corrupted/incomplete cache from looping.
                built = None
                if family == "yoy":
                    candidates = special["yoy"]
                elif family == "record_first":
                    candidates = special["record"]
                elif family == "ambiguous_period":
                    candidates = special["ambiguous"]
                elif family == "unit_trap":
                    candidates = unit_pool
                elif family == "period_trap":
                    candidates = special["period_ytd"] + special["period_annual"] + special["period_fiscal"]
                else:
                    candidates = by_metric.get("revenue", []) + by_metric.get("net_income", [])
                for retry in range(20):
                    try:
                        retry_choice = _pick(candidates, index + retry + family_index * 17, local_rng, fiscal=True)
                        built = _make_claim(bg, snapshots, family, variant, index + retry, retry_choice, local_rng)
                        break
                    except GenerationError as retry_exc:
                        logger.info("retry %s %s/%s/%s: %s", family, variant, index, retry, retry_exc)
                if built is None:
                    raise GenerationError(f"unable to generate {family}/{variant} item {index}") from exc
                row = built
            row["id"] = f"G{generated_index + 1:04d}"
            rows.append(row)
            generated_index += 1
    # Recompute splits with the requested seed after retries.  This keeps the
    # public seed contract independent of the local retry index.
    for index, row in enumerate(rows):
        row["split"] = _split_for(seed, str(row["family"]), str(row["gold_verdict"]), index)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    logger.info("generated %d claims to %s", len(rows), output_path)
    logger.info("counts by family: %s", {family: sum(row["family"] == family for row in rows) for family in FAMILIES})
    logger.info("counts by verdict: %s", {verdict: sum(row["gold_verdict"] == verdict for row in rows) for verdict in ("supported", "contradicted", "insufficient_evidence")})
    return rows


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        generate_claims(seed=args.seed, target=args.target, cache_dir=args.cache_dir, output=args.output, log_path=args.log)
    except (GenerationError, OSError, ValueError) as exc:
        print(f"v2 generation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

