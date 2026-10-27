"""Small, cache-aware SEC EDGAR company-facts client."""

from __future__ import annotations

import hashlib
import json
import re
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


def _quarter_for_end(end: date) -> str:
    return f"{end.year}Q{((end.month - 1) // 3) + 1}"


def _period_from_fact(fact: Mapping[str, Any]) -> str | None:
    start = _date(fact.get("start"))
    end = _date(fact.get("end"))
    if end is None:
        return None
    duration = _days(start, end)
    if duration is None:
        return _quarter_for_end(end)
    if 80 <= duration <= 100:
        return _quarter_for_end(end)
    if 300 <= duration <= 380:
        return f"FY{end.year}"
    frame = str(fact.get("frame") or "")
    match = FRAME_RE.match(frame)
    if match:
        return f"{match.group('year')}{match.group('quarter').upper()}"
    return None


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
    if quarter == 4:
        end = date(year, 12, 31)
    else:
        end = date(year, start_month + 3, 1).fromordinal(
            date(year, start_month + 3, 1).toordinal() - 1
        )
    return start, end


def _is_quarter(period: str) -> bool:
    return bool(re.fullmatch(r"\d{4}Q[1-4]", period, re.I))


def _is_fy(period: str) -> bool:
    return bool(re.fullmatch(r"FY\d{4}", period, re.I))


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

    def _matching_facts(
        self,
        facts: Mapping[str, Any],
        metric: str,
        period: str,
    ) -> tuple[str, str, list[Mapping[str, Any]]] | None:
        target = _period_end_start(period)
        if target is None and period != "latest":
            return None

        for namespace, concept in METRIC_ALIASES[metric]:
            concept_data = facts.get(namespace, {}).get(concept)
            if not isinstance(concept_data, Mapping):
                continue
            preferred_units = METRIC_UNITS.get(metric, ())
            unit_items = list(concept_data.get("units", {}).items())
            unit_items.sort(key=lambda item: (0 if item[0] in preferred_units else 1, item[0]))
            for unit, values in unit_items:
                if not isinstance(values, list):
                    continue
                matching: list[Mapping[str, Any]] = []
                for fact in values:
                    if not isinstance(fact, Mapping):
                        continue
                    end = _date(fact.get("end"))
                    if end is None:
                        continue
                    start = _date(fact.get("start"))
                    duration = _days(start, end)
                    if period == "latest":
                        matching.append(fact)
                        continue
                    target_start, target_end = target  # type: ignore[misc]
                    if _is_quarter(period):
                        direct_duration = (
                            start == target_start
                            and end == target_end
                            and duration is not None
                            and 80 <= duration <= 100
                        )
                        instant_at_period_end = start is None and end == target_end
                        if direct_duration or instant_at_period_end:
                            matching.append(fact)
                    elif _is_fy(period):
                        annual_duration = (
                            start == target_start
                            and end == target_end
                            and duration is not None
                            and 300 <= duration <= 380
                        )
                        instant_at_year_end = start is None and end == target_end
                        if annual_duration or instant_at_year_end:
                            matching.append(fact)
                if matching:
                    matching.sort(
                        key=lambda fact: _fact_sort_key(
                            fact, prefer_direct=period == "latest"
                        ),
                        reverse=True,
                    )
                    return concept, unit, matching
        return None

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
        selected = self._matching_facts(facts, metric, normalized_period)
        if selected is None:
            if _is_quarter(period) and period.endswith("Q4"):
                return self._error(
                    "q4_not_directly_available",
                    available_periods,
                    ticker=resolved["ticker"],
                    cik=resolved["cik"],
                    metric=metric,
                    period=period,
                    message="Q4 is not directly reported as a quarter in the available facts; an annual FY fact was not substituted.",
                )
            return self._error(
                "fact_not_found",
                available_periods,
                ticker=resolved["ticker"],
                cik=resolved["cik"],
                metric=metric,
                period=period,
            )

        concept, unit, matches = selected
        fact = matches[0]
        accn = str(fact.get("accn") or "")
        filing_url = (
            f"{SEC_ARCHIVES_BASE}/{int(resolved['cik'])}/{accn.replace('-', '')}/"
            if accn
            else None
        )
        return {
            "ticker": resolved["ticker"],
            "cik": resolved["cik"],
            "entity": document.get("entityName") or resolved.get("entity"),
            "metric": metric,
            "concept": concept,
            "unit": unit,
            "value": fact.get("val"),
            "start": fact.get("start"),
            "end": fact.get("end"),
            "form": fact.get("form"),
            "accn": accn,
            "filed": fact.get("filed"),
            "frame": fact.get("frame"),
            "filing_url": filing_url,
            "source_sha256": source_sha256,
        }
