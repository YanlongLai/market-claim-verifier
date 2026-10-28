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
    r"^(?:(?P<fy>FY)(?P<fy_year>\d{4})(?P<fy_quarter>Q[1-4])?|(?P<year>\d{4})(?P<quarter>Q[1-4]))$",
    re.I,
)
FISCAL_QUARTER_RE = re.compile(r"^FY(?P<year>\d{4})Q(?P<quarter>[1-4])$", re.I)
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

# Provenance deliberately distinguishes the two US filing families that the
# verifier treats as primary evidence.  The broader ``STATEMENT_FORMS`` set is
# still used for fact selection, while these sets drive the evidence tier.
AUDITED_FORMS = frozenset({"10-K", "10-K/A"})
REVIEWED_FORMS = frozenset({"10-Q", "10-Q/A"})

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


def _fiscal_year_equals_calendar(facts: Mapping[str, Any]) -> bool:
    """Return whether the issuer reports fiscal years ending on December 31."""

    if not isinstance(facts, Mapping):
        return False
    for namespace_data in facts.values():
        if not isinstance(namespace_data, Mapping):
            continue
        for concept_data in namespace_data.values():
            if not isinstance(concept_data, Mapping):
                continue
            units = concept_data.get("units")
            if not isinstance(units, Mapping):
                continue
            for values in units.values():
                if not isinstance(values, list):
                    continue
                for fact in values:
                    if not isinstance(fact, Mapping):
                        continue
                    if str(fact.get("fp") or "").strip().upper() != "FY":
                        continue
                    end = _date(fact.get("end"))
                    fiscal_year = _fact_fiscal_year(fact)
                    if (
                        end is not None
                        and end.month == 12
                        and end.day == 31
                        and fiscal_year == end.year
                    ):
                        return True
    return False


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


def _provenance_value_groups(
    facts: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Group same-period fact values while retaining the filing accessions."""

    groups: list[dict[str, Any]] = []
    for fact in facts:
        value = fact.get("val")
        group = next(
            (
                candidate
                for candidate in groups
                if candidate["value"] == value
            ),
            None,
        )
        if group is None:
            group = {"value": value, "accn": set()}
            groups.append(group)
        accn = str(fact.get("accn") or "").strip()
        if accn:
            group["accn"].add(accn)
    return [
        {"value": group["value"], "accn": sorted(group["accn"])}
        for group in groups
    ]


def _fact_provenance(
    facts: Mapping[str, Any],
    concept: str,
    unit: str,
    start: str | None,
    end: str | None,
    *,
    form_fallback: bool = False,
) -> dict[str, Any]:
    """Summarize all filings reporting one exact XBRL period.

    This intentionally reads the complete companyfacts concept/unit series,
    rather than only the row selected for display.  Comparative rows in later
    filings therefore count as confirmations and differing values are visible
    as restatements.
    """

    matching: list[Mapping[str, Any]] = []
    for namespace_data in facts.values() if isinstance(facts, Mapping) else ():
        if not isinstance(namespace_data, Mapping):
            continue
        concept_data = namespace_data.get(concept)
        if not isinstance(concept_data, Mapping):
            continue
        units = concept_data.get("units")
        values = units.get(unit) if isinstance(units, Mapping) else None
        if not isinstance(values, list):
            continue
        for fact in values:
            if not isinstance(fact, Mapping):
                continue
            fact_start, fact_end = _fact_identity(fact)
            if fact_start == start and fact_end == end:
                matching.append(fact)

    forms = sorted(
        {
            str(fact.get("form") or "").strip().upper()
            for fact in matching
            if str(fact.get("form") or "").strip()
        }
    )
    audited = any(form in AUDITED_FORMS for form in forms)
    reviewed = any(form in REVIEWED_FORMS for form in forms)
    # A non-standard form is not upgraded to audited evidence.  It remains in
    # the L2-shaped direct bucket, with ``form_fallback`` and low strength
    # making that limitation explicit to callers.
    tier = "L1" if audited else "L2" if reviewed else "L2"
    accns = sorted(
        {
            str(fact.get("accn") or "").strip()
            for fact in matching
            if str(fact.get("accn") or "").strip()
        }
    )
    filed = sorted(
        {
            str(fact.get("filed") or "").strip()
            for fact in matching
            if str(fact.get("filed") or "").strip()
        }
    )
    values_seen = _provenance_value_groups(matching)
    restated = len(values_seen) > 1
    amended = any(form.endswith("/A") for form in forms)
    effective_fallback = bool(
        form_fallback
        or (matching and not any(_is_statement_form(fact) for fact in matching))
    )
    if restated or (effective_fallback and len(accns) <= 1):
        strength = "low"
    elif tier == "L1" and len(accns) >= 2:
        strength = "high"
    else:
        strength = "medium"
    result: dict[str, Any] = {
        "tier": tier,
        "audited": audited,
        "confirmations": len(accns),
        "forms": forms,
        "first_filed": filed[0] if filed else None,
        "latest_filed": filed[-1] if filed else None,
        "restated": restated,
        "amended": amended,
        "strength": strength,
    }
    if restated:
        result["values_seen"] = values_seen
    if effective_fallback:
        result["form_fallback"] = True
    return result


def _derived_provenance(
    component_provenance: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build compact L3 provenance for a program-derived fact."""

    components = [dict(value) for value in component_provenance]
    restated = any(bool(value.get("restated")) for value in components)
    fallback = any(bool(value.get("form_fallback")) for value in components)
    filed = sorted(
        str(value.get("first_filed"))
        for value in components
        if value.get("first_filed")
    )
    latest = sorted(
        str(value.get("latest_filed"))
        for value in components
        if value.get("latest_filed")
    )
    result: dict[str, Any] = {
        "tier": "L3",
        "component_tiers": [str(value.get("tier") or "L2") for value in components],
        "component_strengths": [
            str(value.get("strength") or "low") for value in components
        ],
        "audited": False,
        "confirmations": 0,
        "forms": ["derived"],
        "first_filed": filed[0] if filed else None,
        "latest_filed": latest[-1] if latest else None,
        "restated": restated,
        "amended": any(bool(value.get("amended")) for value in components),
        "strength": "low" if restated or fallback else "medium",
    }
    if restated:
        result["values_seen"] = [
            {"component": index, "values_seen": value.get("values_seen", [])}
            for index, value in enumerate(components)
            if value.get("restated")
        ]
    return result


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


def _fact_fiscal_year(fact: Mapping[str, Any]) -> int | None:
    value = fact.get("fy", fact.get("fiscal_year"))
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    return year if 1900 <= year <= 2200 else None


def _fiscal_period_from_fact(fact: Mapping[str, Any]) -> str | None:
    """Return a fiscal-quarter label from SEC ``fy``/``fp`` metadata."""

    fiscal_year = _fact_fiscal_year(fact)
    fiscal_period = str(fact.get("fp") or "").strip().upper()
    if fiscal_year is None or fiscal_period not in {"Q1", "Q2", "Q3", "Q4"}:
        return None
    if _period_type(fact) != "quarter":
        return None
    return f"FY{fiscal_year:04d}{fiscal_period}"


def _is_fiscal_quarter(period: str) -> bool:
    return FISCAL_QUARTER_RE.fullmatch(period) is not None


def _period_basis(period: str, result: Mapping[str, Any] | None = None) -> str:
    label = str(period or "").strip().upper()
    if _is_fiscal_quarter(label) or _is_fy(label):
        return "fiscal"
    if _is_quarter(label):
        return "calendar"
    if result is not None:
        existing = str(result.get("period_basis") or "").strip().lower()
        if existing in {"calendar", "fiscal"}:
            return existing
        resolved = str(result.get("period") or "").strip().upper()
        if _is_fiscal_quarter(resolved) or _is_fy(resolved):
            return "fiscal"
    return "calendar"


def _with_period_metadata(
    result: Mapping[str, Any], requested_period: str
) -> dict[str, Any]:
    value = dict(result)
    period = str(requested_period or "").strip().upper()
    if period == "LATEST":
        fiscal_year = _fact_fiscal_year(value)
        fiscal_period = str(value.get("fiscal_period") or "").strip().upper()
        if fiscal_year is not None and fiscal_period in {"Q1", "Q2", "Q3", "Q4"}:
            period = f"FY{fiscal_year:04d}{fiscal_period}"
        elif fiscal_year is not None and fiscal_period == "FY":
            period = f"FY{fiscal_year:04d}"
        resolved = str(value.get("period") or "").strip().upper()
        if period == "LATEST" and resolved:
            period = resolved
    if period:
        value["period"] = period
    value["period_basis"] = _period_basis(period, value)
    return value


def _history_period_sort_key(period: str) -> tuple[int, int]:
    """Sort comparable history labels from oldest to newest."""

    match = PERIOD_RE.match(period)
    if match is None:
        return (0, 0)
    if match.group("fy"):
        return (
            int(match.group("fy_year")),
            int(match.group("fy_quarter")[1:])
            if match.group("fy_quarter")
            else 4,
        )
    return (int(match.group("year")), int(match.group("quarter")[1:]))


def _history_item_before(
    item: Mapping[str, Any], target: Mapping[str, Any]
) -> bool:
    """Compare history entries by SEC end date, with a label fallback."""

    item_end = _date(item.get("end"))
    target_end = _date(target.get("end"))
    if item_end is not None and target_end is not None:
        return item_end < target_end
    return _history_period_sort_key(str(item["period"])) < _history_period_sort_key(
        str(target["period"])
    )


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
    fiscal_year = _fact_fiscal_year(fact)
    if fiscal_year is not None:
        return fiscal_year == year
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


def _component_from_fact(
    fact: Mapping[str, Any], provenance: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    result = {
        "value": fact.get("val"),
        "start": fact.get("start"),
        "end": fact.get("end"),
        "accn": str(fact.get("accn") or ""),
        "form": fact.get("form"),
        "filed": fact.get("filed"),
        "duration_days": _days(_date(fact.get("start")), _date(fact.get("end"))),
        "period_type": _period_type(fact),
    }
    if provenance is not None:
        result["provenance"] = dict(provenance)
    return result


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

    def companyfacts_snapshot_hashes(self) -> dict[str, str]:
        """Return hashes for companyfacts files actually loaded by this client."""

        return {
            str(filename): str(document_and_hash[1])
            for filename, document_and_hash in self._document_cache.items()
            if str(filename).startswith("companyfacts-")
            and isinstance(document_and_hash, (tuple, list))
            and len(document_and_hash) >= 2
            and document_and_hash[1]
        }

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
                    fiscal_period = _fiscal_period_from_fact(fact)
                    if fiscal_period:
                        periods[fiscal_period] = str(fact.get("end") or "")

        # A fiscal Q4 is often absent as a direct SEC fact.  Add the label when
        # annual minus 9M YTD can derive it, so a model can discover the
        # fiscal interpretation without guessing the issuer's year end.
        if metric in ADDITIVE_METRICS:
            for group in self._fact_groups(facts, metric):
                for candidate in self._derive_candidates_for_group(group):
                    annual = candidate.current
                    fiscal_year = _fact_fiscal_year(annual)
                    if fiscal_year is not None and str(annual.get("fp") or "").upper() == "FY":
                        periods[f"FY{fiscal_year:04d}Q4"] = str(
                            annual.get("end") or ""
                        )
            fiscal_years = {
                fiscal_year
                for group in self._fact_groups(facts, metric)
                for fact in group.values
                if (fiscal_year := _fact_fiscal_year(fact)) is not None
                and str(fact.get("fp") or "").strip().upper() == "FY"
            }
            for fiscal_year in fiscal_years:
                fiscal_label = f"FY{fiscal_year:04d}Q4"
                candidate = self._fiscal_quarter_candidate(
                    facts, metric, fiscal_label
                )
                if candidate is not None:
                    current = (
                        candidate.fact
                        if isinstance(candidate, _SelectedFact)
                        else candidate.current
                    )
                    periods[fiscal_label] = str(current.get("end") or "")
        return [
            period
            for period, _ in sorted(
                periods.items(), key=lambda item: (item[1], item[0]), reverse=True
            )[:8]
        ]

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

    def _history_period_labels(
        self,
        facts: Mapping[str, Any],
        metric: str,
        *,
        period_basis: str = "calendar",
    ) -> list[str]:
        """Return every directly available period plus derivable Q4 labels."""

        labels: set[str] = set()
        groups = self._fact_groups(facts, metric)
        for group in groups:
            selected_facts: Iterable[Mapping[str, Any]] = (
                group.values
                if period_basis == "fiscal"
                else (selected.fact for selected in self._selected_by_period(group).values())
            )
            for fact in selected_facts:
                period = (
                    _fiscal_period_from_fact(fact)
                    if period_basis == "fiscal"
                    else _period_from_fact(fact)
                )
                if period and (
                    _is_quarter(period)
                    or _is_fy(period)
                    or _is_fiscal_quarter(period)
                ):
                    labels.add(period)
            if metric not in ADDITIVE_METRICS:
                continue
            for candidate in self._derive_candidates_for_group(group):
                if candidate.kind != "annual":
                    continue
                end = _date(candidate.current.get("end"))
                if end is not None:
                    if period_basis == "fiscal":
                        fiscal_year = _fact_fiscal_year(candidate.current)
                        if fiscal_year is not None:
                            labels.add(f"FY{fiscal_year:04d}Q4")
                    else:
                        labels.add(f"{end.year}Q4")
        if period_basis == "fiscal" and metric in ADDITIVE_METRICS:
            fiscal_years = {
                fiscal_year
                for group in groups
                for fact in group.values
                if (fiscal_year := _fact_fiscal_year(fact)) is not None
                and str(fact.get("fp") or "").strip().upper() == "FY"
            }
            for fiscal_year in fiscal_years:
                fiscal_label = f"FY{fiscal_year:04d}Q4"
                if self._fiscal_quarter_candidate(facts, metric, fiscal_label) is not None:
                    labels.add(fiscal_label)
        return sorted(labels, key=_history_period_sort_key)

    def history_rank(
        self, ticker: str, metric: str, period: str
    ) -> dict[str, Any]:
        """Rank a fact against all available comparable periods.

        Quarters are compared with quarters, including Q4 values derived from
        annual minus nine-month YTD facts. Fiscal years are compared only with
        fiscal years. ``periods`` is chronological and includes each SEC end
        date so callers can test first-time assertions without reconstructing
        the SEC fact history. Record flags are evaluated through the requested
        period; ``rank`` and ``count`` still describe the full window.
        """

        metric = str(metric or "").strip().lower()
        period = str(period or "").strip().upper()
        if metric not in METRIC_ALIASES:
            return {
                "error": "unknown_metric",
                "ticker": ticker,
                "metric": metric,
                "period": period,
                "period_basis": _period_basis(period),
            }
        if period != "LATEST" and PERIOD_RE.match(period) is None:
            return {
                "error": "invalid_period",
                "ticker": ticker,
                "metric": metric,
                "period": period,
                "period_basis": _period_basis(period),
            }

        target = self.lookup_fact(ticker, metric, period)
        if "error" in target:
            return {
                "ticker": str(ticker).strip().upper(),
                "metric": metric,
                "period": period,
                "period_basis": _period_basis(period),
                "period_type": target.get("period_type", "quarter"),
                "value": None,
                "rank": None,
                "count": None,
                "is_highest": False,
                "is_lowest": False,
                "previous_high": None,
                "previous_low": None,
                "periods_considered": {"first": None, "last": None},
                "periods": [],
                "comparable_periods": [],
                "error": target.get("error", "fact_not_found"),
                "message": target.get(
                    "message", "The requested fact is not available."
                ),
            }

        resolved = self.resolve_ticker(ticker)
        if "error" in resolved:
            return {
                "ticker": str(ticker).strip().upper(),
                "metric": metric,
                "period": period,
                "period_basis": _period_basis(period),
                "period_type": target.get("period_type", "quarter"),
                "value": None,
                "rank": None,
                "count": None,
                "is_highest": False,
                "is_lowest": False,
                "previous_high": None,
                "previous_low": None,
                "periods_considered": {"first": None, "last": None},
                "periods": [],
                "comparable_periods": [],
                "error": resolved.get("error", "unknown_ticker"),
                "message": resolved.get("message", "Ticker could not be resolved."),
            }
        try:
            document, _ = self._facts_document(str(resolved["cik"]))
        except EdgarError as exc:
            return {
                "ticker": resolved.get("ticker", str(ticker).strip().upper()),
                "metric": metric,
                "period": period,
                "period_basis": _period_basis(period),
                "period_type": target.get("period_type", "quarter"),
                "value": None,
                "rank": None,
                "count": None,
                "is_highest": False,
                "is_lowest": False,
                "previous_high": None,
                "previous_low": None,
                "periods_considered": {"first": None, "last": None},
                "periods": [],
                "comparable_periods": [],
                "error": "companyfacts_unavailable",
                "message": str(exc),
            }

        target_period = period
        if period == "LATEST":
            target_period = _period_from_fact(
                {
                    "start": target.get("start"),
                    "end": target.get("end"),
                    "frame": target.get("frame"),
                }
            ) or period
        target_period_type = str(target.get("period_type") or "")
        if target_period_type not in {"quarter", "annual"}:
            return {
                "ticker": resolved["ticker"],
                "metric": metric,
                "period": target_period,
                "period_basis": _period_basis(target_period),
                "period_type": target_period_type,
                "value": target.get("value"),
                "rank": None,
                "count": 0,
                "is_highest": False,
                "is_lowest": False,
                "previous_high": None,
                "previous_low": None,
                "periods_considered": {"first": None, "last": None},
                "periods": [],
                "comparable_periods": [],
                "error": "history_not_supported",
                "message": "History ranking is defined for quarter and annual facts.",
                "provenance": target.get("provenance"),
            }

        period_values: list[dict[str, Any]] = []
        for candidate_period in self._history_period_labels(
            document.get("facts", {}),
            metric,
            period_basis=("fiscal" if _is_fiscal_quarter(period) else "calendar"),
        ):
            candidate = self.lookup_fact(ticker, metric, candidate_period)
            value = candidate.get("value")
            if (
                "error" in candidate
                or candidate.get("period_type") != target_period_type
                or not isinstance(value, (int, float))
                or isinstance(value, bool)
            ):
                continue
            period_values.append(
                {
                    "period": candidate_period,
                    "period_basis": _period_basis(candidate_period),
                    "value": value,
                    "period_type": candidate.get("period_type"),
                    "end": candidate.get("end"),
                    "provenance": candidate.get("provenance"),
                }
            )

        period_values.sort(key=lambda item: _history_period_sort_key(item["period"]))
        target_entry = next(
            (item for item in period_values if item["period"] == target_period),
            None,
        )
        if target_entry is None:
            return {
                "ticker": resolved["ticker"],
                "metric": metric,
                "period": target_period,
                "period_basis": _period_basis(target_period),
                "period_type": target_period_type,
                "value": target.get("value"),
                "rank": None,
                "count": len(period_values),
                "is_highest": False,
                "is_lowest": False,
                "previous_high": None,
                "previous_low": None,
                "periods_considered": {
                    "first": period_values[0]["period"] if period_values else None,
                    "last": period_values[-1]["period"] if period_values else None,
                },
                "periods": period_values,
                "comparable_periods": period_values,
                "error": "fact_not_in_history",
                "message": "The requested fact was not in the comparable history window.",
                "provenance": target.get("provenance"),
            }

        target_value = float(target_entry["value"])
        rank = 1 + sum(
            float(item["value"]) > target_value for item in period_values
        )
        prior = [
            item for item in period_values if _history_item_before(item, target_entry)
        ]
        through_target = [*prior, target_entry]
        previous_high = (
            max(prior, key=lambda item: float(item["value"])) if prior else None
        )
        previous_low = (
            min(prior, key=lambda item: float(item["value"])) if prior else None
        )
        window = {
            "first": period_values[0]["period"] if period_values else None,
            "last": period_values[-1]["period"] if period_values else None,
        }
        return {
            "ticker": resolved["ticker"],
            "metric": metric,
            "period": target_period,
            "period_basis": _period_basis(target_period),
            "period_type": target_period_type,
            "value": target_entry["value"],
            "rank": rank,
            "count": len(period_values),
            "is_highest": all(
                float(item["value"]) <= target_value for item in through_target
            ),
            "is_lowest": all(
                float(item["value"]) >= target_value for item in through_target
            ),
            "previous_high": previous_high,
            "previous_low": previous_low,
            "periods_considered": window,
            "periods": period_values,
            "comparable_periods": period_values,
            "provenance": target_entry.get("provenance") or target.get("provenance"),
        }

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

    def _fiscal_quarter_candidate(
        self,
        facts: Mapping[str, Any],
        metric: str,
        period: str,
    ) -> _SelectedFact | _DerivedCandidate | None:
        """Resolve ``FYyyyyQn`` using the issuer's SEC fiscal metadata."""

        match = FISCAL_QUARTER_RE.fullmatch(period)
        if match is None:
            return None
        fiscal_year = int(match.group("year"))
        quarter = f"Q{match.group('quarter')}"
        groups = self._fact_groups(facts, metric)

        direct_candidates: list[tuple[_FactGroup, list[Mapping[str, Any]], bool]] = []
        for group in groups:
            matching = [
                fact
                for fact in group.values
                if _fiscal_period_from_fact(fact) == period
            ]
            if matching:
                preferred, form_fallback = _preferred_facts(
                    matching, prefer_direct=True
                )
                if preferred:
                    direct_candidates.append((group, preferred, form_fallback))
        if direct_candidates:
            statement_candidates = [
                candidate for candidate in direct_candidates if not candidate[2]
            ]
            group, matching, form_fallback = (
                statement_candidates[0]
                if statement_candidates
                else direct_candidates[0]
            )
            return _SelectedFact(
                group=group,
                fact=matching[0],
                form_fallback=form_fallback,
            )

        if quarter != "Q4" or metric not in ADDITIVE_METRICS:
            return None

        derived_candidates: list[_DerivedCandidate] = []
        for group in groups:
            annual_values = [
                fact
                for fact in group.values
                if _fact_fiscal_year(fact) == fiscal_year
                and str(fact.get("fp") or "").strip().upper() == "FY"
                and _period_type(fact) == "annual"
            ]
            annual_preferred, annual_fallback = _preferred_facts(
                annual_values, prefer_direct=True
            )
            for annual in annual_preferred[:1]:
                annual_start = _date(annual.get("start"))
                annual_end = _date(annual.get("end"))
                if annual_start is None or annual_end is None:
                    continue
                ytd_values = [
                    fact
                    for fact in group.values
                    if _fact_fiscal_year(fact) == fiscal_year
                    and str(fact.get("fp") or "").strip().upper() == "Q3"
                    and _period_type(fact) == "ytd"
                    and _date(fact.get("start")) == annual_start
                    and (_date(fact.get("end")) or date.min) < annual_end
                    and 240
                    <= (_days(_date(fact.get("start")), _date(fact.get("end"))) or 0)
                    <= 300
                ]
                ytd_preferred, ytd_fallback = _preferred_facts(
                    ytd_values, prefer_direct=False
                )
                if not ytd_preferred:
                    continue
                derived_candidates.append(
                    _DerivedCandidate(
                        group=group,
                        current=annual,
                        previous=ytd_preferred[0],
                        form_fallback=annual_fallback or ytd_fallback,
                        derivation=f"FY{fiscal_year} - 9M YTD",
                        kind="annual",
                    )
                )
        if not derived_candidates:
            return None
        non_fallback = [
            candidate for candidate in derived_candidates if not candidate.form_fallback
        ]
        eligible = non_fallback or derived_candidates
        return min(
            eligible,
            key=lambda candidate: (
                candidate.group.order,
                _fact_filed(candidate.current),
            ),
        )

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
        provenance = _fact_provenance(
            document.get("facts", {}),
            selected.group.concept,
            selected.group.unit,
            _fact_identity(fact)[0],
            _fact_identity(fact)[1],
            form_fallback=selected.form_fallback,
        )
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
            "fiscal_year": fact.get("fy"),
            "fiscal_period": fact.get("fp"),
            "duration_days": _days(_date(fact.get("start")), _date(fact.get("end"))),
            "period_type": _period_type(fact),
            "fiscal_equals_calendar": _fiscal_year_equals_calendar(
                document.get("facts", {})
            ),
            "derived": False,
            "filing_url": _filing_url(str(resolved["cik"]), fact),
            "source_sha256": source_sha256,
            "provenance": provenance,
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
        current_provenance = _fact_provenance(
            document.get("facts", {}),
            candidate.group.concept,
            candidate.group.unit,
            _fact_identity(candidate.current)[0],
            _fact_identity(candidate.current)[1],
        )
        previous_provenance = _fact_provenance(
            document.get("facts", {}),
            candidate.group.concept,
            candidate.group.unit,
            _fact_identity(candidate.previous)[0],
            _fact_identity(candidate.previous)[1],
        )
        provenance = _derived_provenance(
            (current_provenance, previous_provenance)
        )
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
            "fiscal_year": candidate.current.get("fy"),
            "fiscal_period": candidate.current.get("fp"),
            "duration_days": _days(derived_start, current_end),
            "period_type": "quarter",
            "fiscal_equals_calendar": _fiscal_year_equals_calendar(
                document.get("facts", {})
            ),
            "derived": True,
            "derivation": candidate.derivation,
            "components": [
                _component_from_fact(candidate.current, current_provenance),
                _component_from_fact(candidate.previous, previous_provenance),
            ],
            "filing_url": None,
            "source_sha256": source_sha256,
            "provenance": provenance,
        }

    def lookup_fact(
        self, ticker: str, metric: str, period: str
    ) -> dict[str, Any]:
        """Return one latest-filed fact for a requested period.

        Calendar quarters use ``YYYYQn``. Fiscal quarters use ``FYyyyyQn``
        and are resolved from SEC ``fy``/``fp`` metadata; fiscal Q4 is
        derived from the annual fact minus the issuer's nine-month YTD fact
        when SEC does not publish a standalone Q4 row.
        """

        metric = str(metric or "").strip().lower()
        period = str(period or "").strip().upper()
        if metric not in METRIC_ALIASES:
            return _with_period_metadata(
                self._error("unknown_metric", [], metric=metric, period=period),
                period,
            )
        if period != "LATEST" and PERIOD_RE.match(period) is None:
            return _with_period_metadata(
                self._error("invalid_period", [], metric=metric, period=period),
                period,
            )
        normalized_period = "latest" if period == "LATEST" else period

        resolved = self.resolve_ticker(ticker)
        if "error" in resolved:
            return _with_period_metadata(
                {
                    **resolved,
                    "metric": metric,
                    "period": period,
                },
                period,
            )
        try:
            document, source_sha256 = self._facts_document(str(resolved["cik"]))
        except EdgarError as exc:
            return _with_period_metadata(
                self._error(
                    "companyfacts_unavailable",
                    [],
                    ticker=resolved.get("ticker"),
                    cik=resolved.get("cik"),
                    metric=metric,
                    period=period,
                    message=str(exc),
                ),
                period,
            )

        facts = document.get("facts", {})
        available_periods = self._available_periods_from_facts(facts, metric)

        if _is_fiscal_quarter(normalized_period):
            fiscal_candidate = self._fiscal_quarter_candidate(
                facts, metric, normalized_period
            )
            if fiscal_candidate is None:
                return _with_period_metadata(
                    self._error(
                        "fact_not_found",
                        available_periods,
                        ticker=resolved["ticker"],
                        cik=resolved["cik"],
                        metric=metric,
                        period=period,
                    ),
                    period,
                )
            if isinstance(fiscal_candidate, _SelectedFact):
                result = self._direct_result(
                    resolved, document, source_sha256, metric, fiscal_candidate
                )
            else:
                result = self._derived_result(
                    resolved, document, source_sha256, metric, fiscal_candidate
                )
            return _with_period_metadata(result, period)

        if normalized_period == "latest":
            latest = self._latest_fact(facts, metric)
            if latest is None:
                return _with_period_metadata(
                    self._error(
                        "fact_not_found",
                        available_periods,
                        ticker=resolved["ticker"],
                        cik=resolved["cik"],
                        metric=metric,
                        period=period,
                    ),
                    period,
                )
            if isinstance(latest, _SelectedFact):
                result = self._direct_result(
                    resolved, document, source_sha256, metric, latest
                )
            else:
                result = self._derived_result(
                    resolved, document, source_sha256, metric, latest
                )
            return _with_period_metadata(result, period)

        details = self._matching_facts_details(facts, metric, normalized_period)
        if details is not None:
            concept, unit, matches, form_fallback = details
            selected = _SelectedFact(
                group=_FactGroup(concept, unit, tuple(matches), 0),
                fact=matches[0],
                form_fallback=form_fallback,
            )
            return _with_period_metadata(
                self._direct_result(
                    resolved, document, source_sha256, metric, selected
                ),
                period,
            )

        if _is_quarter(period) and metric in ADDITIVE_METRICS:
            derived = self._derive_for_period(facts, metric, period)
            if derived is not None:
                return _with_period_metadata(
                    self._derived_result(
                        resolved, document, source_sha256, metric, derived
                    ),
                    period,
                )
        elif _is_quarter(period) and metric in NON_ADDITIVE_METRICS:
            return _with_period_metadata(
                self._error(
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
                ),
                period,
            )

        return _with_period_metadata(
            self._error(
                "fact_not_found",
                available_periods,
                ticker=resolved["ticker"],
                cik=resolved["cik"],
                metric=metric,
                period=period,
            ),
            period,
        )
