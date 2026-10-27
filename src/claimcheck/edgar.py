"""Small, cache-aware SEC EDGAR company-facts client."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import httpx


SEC_DATA_BASE = "https://data.sec.gov"
SEC_FILES_BASE = "https://www.sec.gov/files"
SEC_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"
PERIOD_RE = re.compile(
    r"^(?:(?P<fy>FY)(?P<fy_year>\d{4})|(?P<year>\d{4})(?P<quarter>Q[1-4]))$",
    re.I,
)
FRAME_RE = re.compile(r"^CY(?P<year>\d{4})(?P<quarter>Q[1-4])(?:I)?$", re.I)

STATEMENT_FORMS = frozenset(
    {
        "10-K",
        "10-K/A",
        "10-Q",
        "10-Q/A",
        "20-F",
        "20-F/A",
        "40-F",
        "40-F/A",
    }
)

# These metrics represent additive flows.  A quarter can therefore be
# recovered from cumulative YTD facts, while EPS and share counts cannot.
ADDITIVE_METRICS = frozenset(
    {
        "revenue",
        "net_income",
        "operating_income",
        "gross_profit",
        "capex",
        "rd_expense",
    }
)
NON_ADDITIVE_METRICS = frozenset({"eps_diluted", "shares_outstanding"})

# Each tuple is (taxonomy namespace, concept).  Ordering is intentional:
# modern concepts are preferred, but a period is allowed to fall back to an
# older concept when a company changed its taxonomy usage.
METRIC_ALIASES: dict[str, tuple[tuple[str, str], ...]] = {
    "revenue": (
        ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
        ("us-gaap", "Revenues"),
    ),
    "net_income": (("us-gaap", "NetIncomeLoss"),),
    "operating_income": (("us-gaap", "OperatingIncomeLoss"),),
    "eps_diluted": (("us-gaap", "EarningsPerShareDiluted"),),
    "gross_profit": (("us-gaap", "GrossProfit"),),
    "total_assets": (("us-gaap", "Assets"),),
    "cash": (
        ("us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
        ("us-gaap", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
    ),
    "capex": (("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"),),
    "rd_expense": (("us-gaap", "ResearchAndDevelopmentExpense"),),
    "shares_outstanding": (
        ("dei", "EntityCommonStockSharesOutstanding"),
        ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding"),
    ),
}

METRICS = tuple(METRIC_ALIASES)
METRIC_UNITS: dict[str, tuple[str, ...]] = {
    "revenue": ("USD",),
    "net_income": ("USD",),
    "operating_income": ("USD",),
    "eps_diluted": ("USD/shares",),
    "gross_profit": ("USD",),
    "total_assets": ("USD",),
    "cash": ("USD",),
    "capex": ("USD",),
    "rd_expense": ("USD",),
    "shares_outstanding": ("shares",),
}


Fetcher = Callable[[str], Any]


class EdgarError(RuntimeError):
    """Raised for transport or malformed EDGAR data errors."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _as_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, Mapping):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    if hasattr(value, "content"):
        return bytes(value.content)
    if hasattr(value, "text"):
        return str(value.text).encode("utf-8")
    raise TypeError(f"fetcher returned unsupported value: {type(value).__name__}")


def _json_from_raw(raw: bytes, source: str) -> tuple[dict[str, Any], str]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EdgarError(f"invalid JSON from {source}") from exc
    if not isinstance(value, dict):
        raise EdgarError(f"expected a JSON object from {source}")
    return value, _sha256(raw)


def _date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _days(start: date | None, end: date | None) -> int | None:
    if start is None or end is None:
        return None
    return (end - start).days + 1


def _period_type(fact: Mapping[str, Any]) -> str:
    """Classify a fact using its dates, never the filing's ``fp`` label."""

    start = _date(fact.get("start"))
    end = _date(fact.get("end"))
    if start is None or end is None:
        return "instant"
    duration = _days(start, end)
    if duration is None:
        return "instant"
    if 80 <= duration <= 100:
        return "quarter"
    if 300 <= duration <= 380:
        return "annual"
    # SEC YTD facts are normally 6M or 9M.  Keeping the fallback broad makes
    # the public result schema total even for an unusual 52/53-week calendar.
    return "ytd"


def _fact_identity(fact: Mapping[str, Any]) -> tuple[str | None, str | None]:
    return (
        str(fact.get("start")) if fact.get("start") else None,
        str(fact.get("end")) if fact.get("end") else None,
    )


def _frame_period(fact: Mapping[str, Any]) -> str | None:
    match = FRAME_RE.match(str(fact.get("frame") or ""))
    if not match:
        return None
    return f"{match.group('year')}{match.group('quarter').upper()}"


def _is_statement_form(fact: Mapping[str, Any]) -> bool:
    return str(fact.get("form") or "").strip().upper() in STATEMENT_FORMS


def _value(fact: Mapping[str, Any]) -> int | float | None:
    value = fact.get("val")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


@dataclass(frozen=True)
class _FactGroup:
    concept: str
    unit: str
    values: tuple[Mapping[str, Any], ...]
    order: int


@dataclass(frozen=True)
class _SelectedFact:
    group: _FactGroup
    fact: Mapping[str, Any]
    form_fallback: bool


@dataclass(frozen=True)
class _DerivedCandidate:
    group: _FactGroup
    current: Mapping[str, Any]
    previous: Mapping[str, Any]
    form_fallback: bool
    derivation: str
    kind: str


def _quarter_for_end(end: date) -> str:
    return f"{end.year}Q{((end.month - 1) // 3) + 1}"


def _period_from_fact(fact: Mapping[str, Any]) -> str | None:
    start = _date(fact.get("start"))
    end = _date(fact.get("end"))
    if end is None:
        return None
    frame_period = _frame_period(fact)
    duration = _days(start, end)
    if duration is None:
        return _quarter_for_end(end)
    if 80 <= duration <= 100:
        return frame_period or _quarter_for_end(end)
    if 300 <= duration <= 380:
        return f"FY{end.year}"
    return frame_period


def _period_end_start(period: str) -> tuple[date, date] | None:
    match = PERIOD_RE.match(period)
    if not match:
        return None
    if match.group("fy"):
        year = int(match.group("fy_year"))
        return date(year, 1, 1), date(year, 12, 31)
    year = int(match.group("year"))
    quarter = int(match.group("quarter")[1:])
    start_month = (quarter - 1) * 3 + 1
    start = date(year, start_month, 1)
    next_month = start_month + 3
    if next_month > 12:
        next_month = 1
        next_year = year + 1
    else:
        next_year = year
    end = date(next_year, next_month, 1).fromordinal(
        date(next_year, next_month, 1).toordinal() - 1
    )
    return start, end


def _is_quarter(period: str) -> bool:
    return bool(re.fullmatch(r"\d{4}Q[1-4]", period, re.I))


def _is_fy(period: str) -> bool:
    return bool(re.fullmatch(r"FY\d{4}", period, re.I))


def _matches_annual_period(fact: Mapping[str, Any], period: str) -> bool:
    period_type = _period_type(fact)
    if period_type not in {"annual", "instant"}:
        return False
    year = int(period[2:])
    end = _date(fact.get("end"))
    if end is None:
        return False
    frame = str(fact.get("frame") or "").upper()
    if frame == f"CY{year}":
        return True
    # Annual periods are identified by their end date.  This handles fiscal
    # years such as 2025-07-01..2026-06-30 without treating ``fp=FY`` as a
    # calendar-quarter name.  The fy fallback covers issuers whose facts omit
    # a conventional calendar end year.
    if end.year == year:
        return True
    return fact.get("fy") == year


def _matches_quarter_period(
    fact: Mapping[str, Any], period: str, *, include_ytd: bool = False
) -> bool:
    period_type = _period_type(fact)
    allowed = {"quarter", "instant"}
    if include_ytd:
        allowed.add("ytd")
    if period_type not in allowed:
        return False
    frame_period = _frame_period(fact)
    if frame_period is not None:
        return frame_period == period
    target = _period_end_start(period)
    end = _date(fact.get("end"))
    return target is not None and end == target[1]


def _matches_period(
    fact: Mapping[str, Any], period: str, *, include_ytd: bool = False
) -> bool:
    if _is_quarter(period):
        return _matches_quarter_period(fact, period, include_ytd=include_ytd)
    if _is_fy(period):
        return _matches_annual_period(fact, period)
    return False


def _preferred_facts(
    facts: Iterable[Mapping[str, Any]], *, prefer_direct: bool = False
) -> tuple[list[Mapping[str, Any]], bool]:
    values = list(facts)
    if not values:
        return [], False
    statement_values = [fact for fact in values if _is_statement_form(fact)]
    form_fallback = not statement_values
    preferred = statement_values or values
    preferred.sort(
        key=lambda fact: _fact_sort_key(fact, prefer_direct=prefer_direct),
        reverse=True,
    )
    return preferred, form_fallback


def _duration_phrase(fact: Mapping[str, Any]) -> str:
    duration = _days(_date(fact.get("start")), _date(fact.get("end"))) or 0
    if duration <= 110:
        months = 3
    elif duration <= 220:
        months = 6
    elif duration < 300:
        months = 9
    else:
        months = 12
    return f"{months}M YTD"


def _fact_filed(fact: Mapping[str, Any]) -> str:
    return str(fact.get("filed") or "")


def _fact_sort_key(fact: Mapping[str, Any], *, prefer_direct: bool = False) -> tuple[Any, ...]:
    end = str(fact.get("end") or "")
    filed = _fact_filed(fact)
    start = _date(fact.get("start"))
    end_date = _date(fact.get("end"))
    duration = _days(start, end_date) or 0
    direct_rank = 1 if 80 <= duration <= 100 else 0
    frame_rank = 1 if fact.get("frame") else 0
    return (end, filed, direct_rank if prefer_direct else 0, frame_rank, str(fact.get("accn") or ""))


def _component_from_fact(fact: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "value": fact.get("val"),
        "start": fact.get("start"),
        "end": fact.get("end"),
        "accn": str(fact.get("accn") or ""),
        "form": fact.get("form"),
        "filed": fact.get("filed"),
        "duration_days": _days(_date(fact.get("start")), _date(fact.get("end"))),
        "period_type": _period_type(fact),
    }


def _filing_url(cik: str, fact: Mapping[str, Any]) -> str | None:
    accn = str(fact.get("accn") or "")
    if not accn:
        return None
    return f"{SEC_ARCHIVES_BASE}/{int(cik)}/{accn.replace('-', '')}/"


class EdgarClient:
    """Resolve SEC company facts from disk cache, with injectable transport."""

    def __init__(
        self,
        cache_dir: str | Path = ".cache",
        *,
        fetcher: Fetcher | None = None,
        user_agent: str = "DappGo market-claim-verifier admin@dappgo.com",
        timeout: float = 20.0,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.user_agent = user_agent
        self.timeout = timeout
        self.fetcher = fetcher or self._http_fetch
        self._document_cache: dict[str, tuple[dict[str, Any], str]] = {}

    def _http_fetch(self, url: str) -> bytes:
        response = httpx.get(
            url,
            headers={"User-Agent": self.user_agent},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.content

    def _load_document(self, filename: str, url: str) -> tuple[dict[str, Any], str]:
        if filename in self._document_cache:
            return self._document_cache[filename]

        path = self.cache_dir / filename
        if path.is_file():
            raw = path.read_bytes()
        else:
            try:
                raw = _as_bytes(self.fetcher(url))
            except Exception as exc:  # keep transport failures clear to callers
                raise EdgarError(f"unable to fetch {url}: {exc}") from exc
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            metadata = {
                "fetched_at": _utc_now(),
                "sha256": _sha256(raw),
                "url": url,
            }
            path.with_name(path.name + ".meta.json").write_text(
                json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
            )

        document = _json_from_raw(raw, url)
        self._document_cache[filename] = document
        return document

    def _ticker_document(self) -> tuple[dict[str, Any], str]:
        return self._load_document(
            "company_tickers.json", f"{SEC_FILES_BASE}/company_tickers.json"
        )

    def resolve_ticker(self, ticker: str) -> dict[str, Any]:
        """Return normalized ticker, zero-padded CIK, and entity name."""

        target = str(ticker or "").strip().upper()
        if not target:
            return {"error": "unknown_ticker", "available_periods": []}
        try:
            document, _ = self._ticker_document()
        except EdgarError as exc:
            return {"error": "ticker_map_unavailable", "message": str(exc), "available_periods": []}

        records: Iterable[Any]
        if isinstance(document.get("data"), list):
            records = document["data"]
        else:
            records = document.values()
        for record in records:
            if not isinstance(record, Mapping):
                continue
            if str(record.get("ticker") or "").strip().upper() != target:
                continue
            try:
                cik = f"{int(record.get('cik_str')):010d}"
            except (TypeError, ValueError):
                return {"error": "invalid_cik", "available_periods": []}
            return {
                "ticker": target,
                "cik": cik,
                "entity": str(record.get("title") or target),
            }
        return {"error": "unknown_ticker", "ticker": target, "available_periods": []}

    def _facts_document(self, cik: str) -> tuple[dict[str, Any], str]:
        filename = f"companyfacts-CIK{cik}.json"
        url = f"{SEC_DATA_BASE}/api/xbrl/companyfacts/CIK{cik}.json"
        return self._load_document(filename, url)

    @staticmethod
    def _error(
        error: str,
        available_periods: list[str],
        **extra: Any,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {"error": error, "available_periods": available_periods}
        result.update(extra)
        return result

    def _available_periods_from_facts(
        self, facts: Mapping[str, Any], metric: str
    ) -> list[str]:
        periods: dict[str, str] = {}
        for namespace, concept in METRIC_ALIASES[metric]:
            concept_data = facts.get(namespace, {}).get(concept, {})
            for values in concept_data.get("units", {}).values():
                if not isinstance(values, list):
                    continue
                for fact in values:
                    if not isinstance(fact, Mapping):
                        continue
                    period = _period_from_fact(fact)
                    if period:
                        periods[period] = str(fact.get("end") or "")
        return [period for period, _ in sorted(periods.items(), key=lambda item: item[1], reverse=True)[:8]]

    def list_periods(self, ticker: str, metric: str) -> list[str] | dict[str, Any]:
        """List directly queryable quarter/FY periods, newest first."""

        metric = str(metric or "").strip().lower()
        if metric not in METRIC_ALIASES:
            return self._error("unknown_metric", [], metric=metric)
        resolved = self.resolve_ticker(ticker)
        if "error" in resolved:
            return resolved
        try:
            document, _ = self._facts_document(str(resolved["cik"]))
        except EdgarError as exc:
            return self._error("companyfacts_unavailable", [], message=str(exc))
        return self._available_periods_from_facts(document.get("facts", {}), metric)

    def _fact_groups(
        self, facts: Mapping[str, Any], metric: str
    ) -> list[_FactGroup]:
        groups: list[_FactGroup] = []
        order = 0
        for namespace, concept in METRIC_ALIASES[metric]:
            concept_data = facts.get(namespace, {}).get(concept)
            if not isinstance(concept_data, Mapping):
                continue
            preferred_units = METRIC_UNITS.get(metric, ())
            unit_items = list(concept_data.get("units", {}).items())
            unit_items.sort(
                key=lambda item: (0 if item[0] in preferred_units else 1, item[0])
            )
            for unit, values in unit_items:
                if not isinstance(values, list):
                    continue
                valid_values = tuple(
                    fact
                    for fact in values
                    if isinstance(fact, Mapping) and _date(fact.get("end")) is not None
                )
                if not valid_values:
                    continue
                groups.append(_FactGroup(concept, str(unit), valid_values, order))
                order += 1
        return groups

    @staticmethod
    def _selected_by_period(group: _FactGroup) -> dict[
        tuple[str | None, str | None], _SelectedFact
    ]:
        by_identity: dict[
            tuple[str | None, str | None], list[Mapping[str, Any]]
        ] = {}
        for fact in group.values:
            by_identity.setdefault(_fact_identity(fact), []).append(fact)
        selected: dict[tuple[str | None, str | None], _SelectedFact] = {}
        for identity, values in by_identity.items():
            preferred, form_fallback = _preferred_facts(values, prefer_direct=True)
            if preferred:
                selected[identity] = _SelectedFact(
                    group=group,
                    fact=preferred[0],
                    form_fallback=form_fallback,
                )
        return selected

    def _latest_selected_facts(
        self, groups: Iterable[_FactGroup]
    ) -> list[_SelectedFact]:
        by_identity: dict[
            tuple[str | None, str | None], list[tuple[_FactGroup, Mapping[str, Any]]]
        ] = {}
        for group in groups:
            for fact in group.values:
                by_identity.setdefault(_fact_identity(fact), []).append((group, fact))

        selected: list[_SelectedFact] = []
        for entries in by_identity.values():
            statement_entries = [
                entry for entry in entries if _is_statement_form(entry[1])
            ]
            eligible = statement_entries or entries
            form_fallback = not statement_entries
            group = min(eligible, key=lambda entry: entry[0].order)[0]
            group_values = [fact for candidate_group, fact in eligible if candidate_group == group]
            preferred, _ = _preferred_facts(group_values, prefer_direct=True)
            if preferred:
                selected.append(
                    _SelectedFact(group, preferred[0], form_fallback)
                )
        return selected

    def _matching_facts_details(
        self,
        facts: Mapping[str, Any],
        metric: str,
        period: str,
    ) -> tuple[str, str, list[Mapping[str, Any]], bool] | None:
        if period == "latest":
            return None

        candidates: list[
            tuple[_FactGroup, list[Mapping[str, Any]], bool]
        ] = []
        for group in self._fact_groups(facts, metric):
            matching = [
                fact
                for fact in group.values
                if _matches_period(fact, period)
            ]
            if matching:
                preferred, form_fallback = _preferred_facts(
                    matching, prefer_direct=True
                )
                candidates.append((group, preferred, form_fallback))

        if not candidates:
            return None
        # Form preference outranks concept-alias preference.  Within the
        # statement-form or fallback tier, the modern concept/unit wins.
        statement_candidates = [candidate for candidate in candidates if not candidate[2]]
        group, matching, form_fallback = (
            statement_candidates[0] if statement_candidates else candidates[0]
        )
        return group.concept, group.unit, matching, form_fallback

    def _matching_facts(
        self,
        facts: Mapping[str, Any],
        metric: str,
        period: str,
    ) -> tuple[str, str, list[Mapping[str, Any]]] | None:
        """Backward-compatible three-field view of period matches."""

        details = self._matching_facts_details(facts, metric, period)
        if details is None:
            return None
        concept, unit, matching, _ = details
        return concept, unit, matching

    @staticmethod
    def _candidate_period_matches(
        candidate: _DerivedCandidate, period: str
    ) -> bool:
        current = candidate.current
        if candidate.kind == "annual":
            end = _date(current.get("end"))
            return end is not None and _quarter_for_end(end) == period
        frame_period = _frame_period(current)
        end = _date(current.get("end"))
        label = frame_period or (_quarter_for_end(end) if end else None)
        return label == period

    @staticmethod
    def _derive_candidates_for_group(
        group: _FactGroup,
    ) -> list[_DerivedCandidate]:
        selected = EdgarClient._selected_by_period(group)
        values = list(selected.values())
        candidates: list[_DerivedCandidate] = []
        for current_selected in values:
            current = current_selected.fact
            current_type = _period_type(current)
            current_start = _date(current.get("start"))
            current_end = _date(current.get("end"))
            if current_start is None or current_end is None:
                continue
            if current_type == "ytd":
                previous_options = [
                    selected_fact
                    for selected_fact in values
                    if _date(selected_fact.fact.get("start")) == current_start
                    and (_date(selected_fact.fact.get("end")) or date.min) < current_end
                    and _period_type(selected_fact.fact) in {"quarter", "ytd"}
                ]
                if not previous_options:
                    continue
                previous_selected = max(
                    previous_options,
                    key=lambda item: _date(item.fact.get("end")) or date.min,
                )
                previous_end = _date(previous_selected.fact.get("end"))
                if previous_end is None:
                    continue
                if _value(current) is None or _value(previous_selected.fact) is None:
                    continue
                candidates.append(
                    _DerivedCandidate(
                        group=group,
                        current=current,
                        previous=previous_selected.fact,
                        form_fallback=(
                            current_selected.form_fallback
                            or previous_selected.form_fallback
                        ),
                        derivation=(
                            f"{_duration_phrase(current)} - "
                            f"{_duration_phrase(previous_selected.fact)}"
                        ),
                        kind="ytd",
                    )
                )
            elif current_type == "annual":
                ytd_options = [
                    selected_fact
                    for selected_fact in values
                    if _date(selected_fact.fact.get("start")) == current_start
                    and (_date(selected_fact.fact.get("end")) or date.min) < current_end
                    and _period_type(selected_fact.fact) == "ytd"
                    and 240 <= (
                        _days(
                            _date(selected_fact.fact.get("start")),
                            _date(selected_fact.fact.get("end")),
                        )
                        or 0
                    ) <= 300
                ]
                if not ytd_options:
                    continue
                ytd_selected = max(
                    ytd_options,
                    key=lambda item: _date(item.fact.get("end")) or date.min,
                )
                if _value(current) is None or _value(ytd_selected.fact) is None:
                    continue
                fiscal_year = current_end.year
                candidates.append(
                    _DerivedCandidate(
                        group=group,
                        current=current,
                        previous=ytd_selected.fact,
                        form_fallback=(
                            current_selected.form_fallback
                            or ytd_selected.form_fallback
                        ),
                        derivation=f"FY{fiscal_year} - 9M YTD",
                        kind="annual",
                    )
                )
        return candidates

    def _derive_for_period(
        self,
        facts: Mapping[str, Any],
        metric: str,
        period: str,
    ) -> _DerivedCandidate | None:
        candidates = [
            candidate
            for group in self._fact_groups(facts, metric)
            for candidate in self._derive_candidates_for_group(group)
            if self._candidate_period_matches(candidate, period)
        ]
        if not candidates:
            return None
        non_fallback = [candidate for candidate in candidates if not candidate.form_fallback]
        eligible = non_fallback or candidates
        return min(
            eligible,
            key=lambda candidate: (
                candidate.group.order,
                _fact_filed(candidate.current),
            ),
        )

    def _latest_fact(
        self,
        facts: Mapping[str, Any],
        metric: str,
    ) -> _SelectedFact | _DerivedCandidate | None:
        groups = self._fact_groups(facts, metric)
        selected = self._latest_selected_facts(groups)
        if not selected:
            return None

        instant = [
            item
            for item in selected
            if _period_type(item.fact) == "instant"
        ]
        if instant:
            return max(
                instant,
                key=lambda item: (
                    str(item.fact.get("end") or ""),
                    _fact_filed(item.fact),
                    -item.group.order,
                ),
            )

        direct_quarters = [
            item
            for item in selected
            if _period_type(item.fact) == "quarter"
        ]
        derived = (
            [
                candidate
                for group in groups
                for candidate in self._derive_candidates_for_group(group)
            ]
            if metric in ADDITIVE_METRICS
            else []
        )
        latest_direct = max(
            direct_quarters,
            key=lambda item: (
                str(item.fact.get("end") or ""),
                _fact_filed(item.fact),
                -item.group.order,
            ),
            default=None,
        )
        latest_derived = max(
            derived,
            key=lambda candidate: (
                str(candidate.current.get("end") or ""),
                _fact_filed(candidate.current),
                -candidate.group.order,
            ),
            default=None,
        )
        if latest_direct is not None and latest_derived is not None:
            direct_end = str(latest_direct.fact.get("end") or "")
            derived_end = str(latest_derived.current.get("end") or "")
            if direct_end >= derived_end:
                return latest_direct
            return latest_derived
        if latest_direct is not None:
            return latest_direct
        if latest_derived is not None:
            return latest_derived

        fallback = [
            item
            for item in selected
            if _period_type(item.fact) in {"ytd", "annual"}
        ]
        if not fallback:
            return None
        return max(
            fallback,
            key=lambda item: (
                str(item.fact.get("end") or ""),
                _fact_filed(item.fact),
                -item.group.order,
            ),
        )

    def _direct_result(
        self,
        resolved: Mapping[str, Any],
        document: Mapping[str, Any],
        source_sha256: str,
        metric: str,
        selected: _SelectedFact,
    ) -> dict[str, Any]:
        fact = selected.fact
        accn = str(fact.get("accn") or "")
        return {
            "ticker": resolved["ticker"],
            "cik": resolved["cik"],
            "entity": document.get("entityName") or resolved.get("entity"),
            "metric": metric,
            "concept": selected.group.concept,
            "unit": selected.group.unit,
            "value": fact.get("val"),
            "start": fact.get("start"),
            "end": fact.get("end"),
            "form": fact.get("form"),
            "form_fallback": selected.form_fallback,
            "accn": accn,
            "filed": fact.get("filed"),
            "frame": fact.get("frame"),
            "duration_days": _days(_date(fact.get("start")), _date(fact.get("end"))),
            "period_type": _period_type(fact),
            "derived": False,
            "filing_url": _filing_url(str(resolved["cik"]), fact),
            "source_sha256": source_sha256,
        }

    def _derived_result(
        self,
        resolved: Mapping[str, Any],
        document: Mapping[str, Any],
        source_sha256: str,
        metric: str,
        candidate: _DerivedCandidate,
    ) -> dict[str, Any]:
        current_value = _value(candidate.current)
        previous_value = _value(candidate.previous)
        current_end = _date(candidate.current.get("end"))
        previous_end = _date(candidate.previous.get("end"))
        if (
            current_value is None
            or previous_value is None
            or current_end is None
            or previous_end is None
        ):
            raise ValueError("derived components must have numeric values and dates")
        derived_start = previous_end.fromordinal(previous_end.toordinal() + 1)
        derived_value = current_value - previous_value
        return {
            "ticker": resolved["ticker"],
            "cik": resolved["cik"],
            "entity": document.get("entityName") or resolved.get("entity"),
            "metric": metric,
            "concept": candidate.group.concept,
            "unit": candidate.group.unit,
            "value": derived_value,
            "start": derived_start.isoformat(),
            "end": current_end.isoformat(),
            "form": "derived",
            "form_fallback": candidate.form_fallback,
            "accn": None,
            "filed": max(
                _fact_filed(candidate.current), _fact_filed(candidate.previous)
            )
            or None,
            "frame": _frame_period(candidate.current),
            "duration_days": _days(derived_start, current_end),
            "period_type": "quarter",
            "derived": True,
            "derivation": candidate.derivation,
            "components": [
                _component_from_fact(candidate.current),
                _component_from_fact(candidate.previous),
            ],
            "filing_url": None,
            "source_sha256": source_sha256,
        }

    def lookup_fact(
        self, ticker: str, metric: str, period: str
    ) -> dict[str, Any]:
        """Return one latest-filed fact for a requested period."""

        metric = str(metric or "").strip().lower()
        period = str(period or "").strip().upper()
        if metric not in METRIC_ALIASES:
            return self._error("unknown_metric", [], metric=metric, period=period)
        if period != "LATEST" and PERIOD_RE.match(period) is None:
            return self._error("invalid_period", [], metric=metric, period=period)
        normalized_period = "latest" if period == "LATEST" else period

        resolved = self.resolve_ticker(ticker)
        if "error" in resolved:
            return {
                **resolved,
                "metric": metric,
                "period": period,
            }
        try:
            document, source_sha256 = self._facts_document(str(resolved["cik"]))
        except EdgarError as exc:
            return self._error(
                "companyfacts_unavailable",
                [],
                ticker=resolved.get("ticker"),
                cik=resolved.get("cik"),
                metric=metric,
                period=period,
                message=str(exc),
            )

        facts = document.get("facts", {})
        available_periods = self._available_periods_from_facts(facts, metric)
        if normalized_period == "latest":
            latest = self._latest_fact(facts, metric)
            if latest is None:
                return self._error(
                    "fact_not_found",
                    available_periods,
                    ticker=resolved["ticker"],
                    cik=resolved["cik"],
                    metric=metric,
                    period=period,
                )
            if isinstance(latest, _SelectedFact):
                return self._direct_result(
                    resolved, document, source_sha256, metric, latest
                )
            return self._derived_result(
                resolved, document, source_sha256, metric, latest
            )

        details = self._matching_facts_details(facts, metric, normalized_period)
        if details is not None:
            concept, unit, matches, form_fallback = details
            selected = _SelectedFact(
                group=_FactGroup(concept, unit, tuple(matches), 0),
                fact=matches[0],
                form_fallback=form_fallback,
            )
            return self._direct_result(
                resolved, document, source_sha256, metric, selected
            )

        if _is_quarter(period) and metric in ADDITIVE_METRICS:
            derived = self._derive_for_period(facts, metric, period)
            if derived is not None:
                return self._derived_result(
                    resolved, document, source_sha256, metric, derived
                )
        elif _is_quarter(period) and metric in NON_ADDITIVE_METRICS:
            return self._error(
                "not_additive_cannot_derive",
                available_periods,
                ticker=resolved["ticker"],
                cik=resolved["cik"],
                metric=metric,
                period=period,
                message=(
                    "The requested quarter is not directly available and "
                    f"{metric} is non-additive, so it cannot be derived."
                ),
            )

        return self._error(
            "fact_not_found",
            available_periods,
            ticker=resolved["ticker"],
            cik=resolved["cik"],
            metric=metric,
            period=period,
        )
