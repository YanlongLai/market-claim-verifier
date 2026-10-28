#!/usr/bin/env python3
"""Sample and paraphrase generated v2 claims through the provider layer."""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
DEFAULT_INPUT = ROOT / "eval" / "v2" / "claims-generated.jsonl"
DEFAULT_OUTPUT = ROOT / "eval" / "v2" / "claims-paraphrased.jsonl"
DEFAULT_TRACES = ROOT / "eval" / "v2" / "traces"
DEFAULT_LEDGER = ROOT / "eval" / "v2" / "ledger.jsonl"
DEFAULT_PROMPT = ROOT / "prompts" / "v2-paraphrase.md"
DEFAULT_PROVIDER = "baseten"
DEFAULT_MODEL = "meta-models/muse-spark-open-1026"
DEFAULT_SEED = 20261027
DEFAULT_SAMPLE = 60
DEFAULT_OUTPUT_TOKENS = 256

COMPANY_ALIASES = {
    "AAPL": ("apple", "aapl"), "MSFT": ("microsoft", "msft"),
    "NVDA": ("nvidia", "nvda"), "AMZN": ("amazon", "amzn"),
    "GOOGL": ("alphabet", "google", "googl"), "META": ("meta", "meta platforms"),
    "TSLA": ("tesla", "tsla"), "JPM": ("jpmorgan", "jpmorgan chase", "jpm"),
    "V": ("visa", " v "), "WMT": ("walmart", "wmt"),
    "XOM": ("exxon mobil", "exxonmobil", "xom"), "JNJ": ("johnson & johnson", "jnj"),
    "UNH": ("unitedhealth", "unitedhealth group", "unh"), "NFLX": ("netflix", "nflx"),
    "ORCL": ("oracle", "orcl"), "ADBE": ("adobe", "adbe"),
    "COST": ("costco", "cost"), "NKE": ("nike", "nke"),
    "CSCO": ("cisco", "csco"), "INTC": ("intel", "intc"),
    "AMD": ("amd",), "CRM": ("salesforce", "crm"),
    "KO": ("coca-cola", "coca cola", "ko"), "PEP": ("pepsico", "pep"),
}
NUMBER_RE = re.compile(
    r"(?P<negative>-)?\s*(?P<currency>[$€£])?\s*(?P<number>\d[\d,]*(?:\.\d+)?)\s*"
    r"(?P<unit>trillion|billion|million|thousand|tn|bn|mm|k|t|b|m)?\s*"
    r"(?P<percent>%|percent)?",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(20\d{2})\b")
QUARTER_RE = re.compile(r"\b(?:Q|quarter\s*)([1-4])\b", re.IGNORECASE)
ORDINAL_QUARTER_RE = re.compile(r"\b(first|second|third|fourth)\s+quarter\b", re.IGNORECASE)
MONTH_RE = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.IGNORECASE,
)


class ParaphraseError(RuntimeError):
    """Raised for invalid paraphrase inputs or provider responses."""


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ParaphraseError(f"{source}:{line_number} is not an object")
            result.append(value)
    return result


def _number_token(value: str, unit: str | None, currency: str | None, percent: str | None, negative: bool = False) -> tuple[str, str, str]:
    try:
        numeric = Decimal(value.replace(",", ""))
    except InvalidOperation:
        return value.replace(",", ""), "", "percent" if percent else "plain"
    unit_key = (unit or "").lower()
    multiplier = {
        "": Decimal(1), "k": Decimal(1_000), "thousand": Decimal(1_000),
        "m": Decimal(1_000_000), "mm": Decimal(1_000_000), "million": Decimal(1_000_000),
        "b": Decimal(1_000_000_000), "bn": Decimal(1_000_000_000), "billion": Decimal(1_000_000_000),
        "t": Decimal(1_000_000_000_000), "tn": Decimal(1_000_000_000_000), "trillion": Decimal(1_000_000_000_000),
    }.get(unit_key, Decimal(1))
    kind = "percent" if percent else "currency" if currency or unit_key else "plain"
    numeric *= -1 if negative else 1
    formatted = format(numeric * multiplier, "f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    # The exact numeric phrase may be rendered as $47.5B, $47.5 billion, or
    # $47,500 million; compare the canonical base-unit value and semantic kind.
    return formatted or "0", "", kind


def extract_number_phrases(text: str) -> list[tuple[str, str, str]]:
    """Return canonical numeric requirements, excluding bare years and ordinals."""

    found: list[tuple[str, str, str]] = []
    for match in NUMBER_RE.finditer(text):
        raw = match.group(0).strip()
        number = match.group("number")
        if not number or (not match.group("currency") and not match.group("unit") and not match.group("percent")):
            continue
        if re.fullmatch(r"20\d{2}", number.replace(",", "")):
            continue
        token = _number_token(number, match.group("unit"), match.group("currency"), match.group("percent"), bool(match.group("negative")))
        if token not in found:
            found.append(token)
    return found


def _direction_groups(text: str) -> set[str]:
    lowered = text.casefold().replace("-", " ")
    groups: dict[str, tuple[str, ...]] = {
        "up": ("up", "rose", "rise", "increased", "increase", "grew", "growth", "higher", "gain"),
        "down": ("down", "fell", "fall", "decreased", "decrease", "declined", "decline", "lower", "drop"),
        "above": ("topped", "top", "above", "over", "exceeded", "cleared", "at least", "more than"),
        "below": ("below", "under", "less than", "fewer than"),
        "approx": ("about", "roughly", "approximately", "around", "near", "close to"),
        "record": ("record", "first time", "first-ever", "new high", "surpassed"),
        "yoy": ("year over year", "year-over-year", "yoy", "from a year earlier"),
    }
    return {name for name, words in groups.items() if any(word in lowered for word in words)}


def _period_groups(text: str) -> set[str]:
    """Classify period wording so a rewrite cannot silently change its basis."""

    lowered = text.casefold().replace("-", " ")
    groups: set[str] = set()
    if re.search(r"\b(fiscal|fy\s*20\d{2})\b", lowered):
        groups.add("fiscal")
    if re.search(r"\bcalendar\b", lowered):
        groups.add("calendar")
    if (
        re.search(r"\b(ytd|year\s+to\s+date)\b", lowered)
        or re.search(r"\b(?:first|three|six|nine|twelve)\s+months?\b", lowered)
        or re.search(r"\b\d+\s+month(?:s)?\b", lowered)
    ):
        groups.add("ytd")
    if (
        re.search(r"\b(annual|full year|year ended|year ending|fiscal year)\b", lowered)
        or re.search(r"\bfiscal\s+20\d{2}\b", lowered)
        or re.search(r"\bfy\s*20\d{2}\b", lowered)
    ):
        groups.add("annual")
    if (
        QUARTER_RE.search(lowered)
        or ORDINAL_QUARTER_RE.search(lowered)
        or re.search(r"\bquarter\b", lowered)
        or re.search(r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+quarter\b", lowered)
    ):
        groups.add("quarter")
    return groups


def _period_requirements(text: str, spec: Mapping[str, Any] | None) -> tuple[set[str], set[int]]:
    years = {int(value) for value in YEAR_RE.findall(text)}
    quarters: set[int] = set()
    for match in QUARTER_RE.finditer(text):
        try:
            quarters.add(int(match.group(1)))
        except ValueError:
            pass
    ordinal_values = {"first": 1, "second": 2, "third": 3, "fourth": 4}
    quarters.update(ordinal_values[name.casefold()] for name in ORDINAL_QUARTER_RE.findall(text))
    if spec and not years and not quarters:
        for key in ("period", "fiscal_period", "quarter_period", "annual_period"):
            value = spec.get(key)
            if value is None:
                continue
            years.update(int(item) for item in YEAR_RE.findall(str(value)))
            quarters.update(int(item) for item in re.findall(r"Q([1-4])", str(value), re.IGNORECASE))
            break
    return years, quarters


def _month_quarters(text: str) -> set[int]:
    month_numbers = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    }
    return {(month_numbers[name.casefold()] - 1) // 3 + 1 for name in MONTH_RE.findall(text)}


def _company_present(text: str, ticker: str | None) -> bool:
    if not ticker:
        return True
    lowered = f" {text.casefold()} "
    return any(alias.casefold() in lowered for alias in COMPANY_ALIASES.get(ticker.upper(), (ticker,)))


MAX_PARAPHRASE_WORDS = 35
COMMENTARY_WORDS = (
    "claim", "unverified", "verify", "verified", "accurate", "inaccurate", "cannot confirm", "knowledge cutoff",
    "I", "I'm", "I don't",
)


def check_paraphrase_constraints(
    original: str,
    rewritten: str,
    *,
    spec: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Check the hard preservation rules used after every model response."""

    reasons: list[str] = []
    if not isinstance(rewritten, str) or not rewritten.strip():
        return {"accepted": False, "reasons": ["empty paraphrase"], "required_numbers": [], "found_numbers": []}
    # The model sometimes fact-checks the claim instead of rewriting it (e.g. "That claim is not accurate - Tesla's
    # revenue did not increase"). A paraphrase must be one short line with no commentary about the claim itself.
    if "\n" in rewritten.strip():
        reasons.append("not a single line")
    if len(rewritten.split()) > MAX_PARAPHRASE_WORDS:
        reasons.append(f"longer than {MAX_PARAPHRASE_WORDS} words")
    commentary = sorted(word for word in COMMENTARY_WORDS if re.search(rf"\b{word}\b", rewritten, re.IGNORECASE))
    if commentary:
        reasons.append("commentary instead of paraphrase: " + ", ".join(commentary))
    required_numbers = extract_number_phrases(original)
    found_numbers = extract_number_phrases(rewritten)
    found_number_counts = Counter(found_numbers)
    for token, required_count in Counter(required_numbers).items():
        if found_number_counts[token] < required_count:
            reasons.append(f"missing number phrase {token[0]} ({token[2]})")
    ticker = str(spec.get("ticker") or "").upper() if isinstance(spec, Mapping) else None
    if not ticker and isinstance(spec, Mapping) and isinstance(spec.get("parts"), list):
        tickers = {str(part.get("ticker") or "").upper() for part in spec["parts"] if isinstance(part, Mapping)}
        if any(not _company_present(rewritten, item) for item in tickers if item):
            reasons.append("missing company identity")
    elif not _company_present(rewritten, ticker):
        reasons.append("missing company identity")
    original_years, original_quarters = _period_requirements(original, spec)
    rewritten_years, rewritten_quarters = _period_requirements(rewritten, None)
    if original_years and not original_years <= rewritten_years:
        reasons.append("missing period year")
    if original_quarters and not original_quarters <= rewritten_quarters:
        # Q3 2025 and “the September quarter” are allowed synonyms.
        if not (original_quarters & (_month_quarters(rewritten) | rewritten_quarters)):
            reasons.append("missing period quarter")
    source_period_groups = _period_groups(original)
    target_period_groups = _period_groups(rewritten)
    for group in sorted(source_period_groups):
        if group not in target_period_groups:
            reasons.append(f"missing period semantics: {group}")
    source_groups = _direction_groups(original)
    target_groups = _direction_groups(rewritten)
    for group in sorted(source_groups):
        if group not in target_groups:
            reasons.append(f"missing direction semantics: {group}")
    return {
        "accepted": not reasons,
        "reasons": reasons,
        "required_numbers": required_numbers,
        "found_numbers": found_numbers,
        "required_years": sorted(original_years),
        "required_quarters": sorted(original_quarters),
        "direction_groups": sorted(source_groups),
    }


constraint_checker = check_paraphrase_constraints


def select_sample(claims: Sequence[Mapping[str, Any]], *, sample_size: int = DEFAULT_SAMPLE, seed: int = DEFAULT_SEED) -> list[dict[str, Any]]:
    """Pick a stable sample while retaining both splits when available."""

    if sample_size <= 0:
        return []
    rng = random.Random(seed)
    items = [dict(item) for item in claims]
    if len(items) <= sample_size:
        return items
    dev = [item for item in items if item.get("split") == "dev"]
    test = [item for item in items if item.get("split") == "test"]
    selected: list[dict[str, Any]] = []
    if dev and test and sample_size >= 2:
        selected.extend([rng.choice(dev), rng.choice(test)])
        remaining = [item for item in items if item.get("id") not in {selected[0].get("id"), selected[1].get("id")}]
        selected.extend(rng.sample(remaining, sample_size - 2))
    else:
        selected = rng.sample(items, sample_size)
    return sorted(selected, key=lambda item: str(item.get("id")))


class _DryRunChatClient:
    def __init__(self) -> None:
        self.chat = self
        self.completions = self
        self.responses = self

    def create(self, **kwargs: Any) -> dict[str, Any]:
        messages = kwargs.get("messages") or []
        claim = ""
        if messages:
            for message in reversed(messages):
                if isinstance(message, Mapping) and message.get("role") == "user":
                    claim = str(message.get("content") or "")
                    break
        else:
            inputs = kwargs.get("input") or []
            for message in reversed(inputs):
                if isinstance(message, Mapping) and message.get("role") == "user":
                    claim = str(message.get("content") or "")
                    break
        output = f"Breaking: {claim}"
        return {
            "status": "completed",
            "output_text": output,
            "choices": [{"message": {"content": output}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 120, "completion_tokens": 24},
        }


def _prompt_text(prompt_path: str | Path = DEFAULT_PROMPT) -> str:
    return Path(prompt_path).read_text(encoding="utf-8")


def _payload(adapter: Any, claim: str, prompt: str, model: str, max_output_tokens: int) -> dict[str, Any]:
    if adapter.chat_completions:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": claim},
            ],
            "max_tokens": max_output_tokens,
        }
    return {
        "model": model,
        "instructions": prompt,
        "input": [{"role": "user", "content": claim}],
        "max_output_tokens": max_output_tokens,
    }


def _response_text(response: Any) -> str:
    value = getattr(response, "text", None)
    if value is not None:
        return str(value).strip().strip("`").strip()
    if isinstance(response, Mapping):
        return str(response.get("output_text") or response.get("text") or "").strip()
    return str(value or "").strip()


def _request_once(
    claim: str,
    *,
    adapter: Any,
    client: Any,
    ledger: Any,
    recorder: Any,
    prompt: str,
    model: str,
    max_output_tokens: int,
    provider: str,
) -> str:
    request = _payload(adapter, claim, prompt, model, max_output_tokens)
    reservation = ledger.reserve(request, model=model, max_output_tokens=max_output_tokens, provider=provider)
    started = time.perf_counter()
    try:
        response = adapter.call(client, request)
    except Exception as exc:
        recorder.record_request(
            payload=request, response={"error": type(exc).__name__, "message": str(exc)},
            reservation=reservation, usage=None, cost=reservation.amount,
            latency_ms=(time.perf_counter() - started) * 1000, status="error",
        )
        raise
    latency_ms = (time.perf_counter() - started) * 1000
    cost = ledger.reconcile(reservation, response.usage)
    recorder.record_request(
        payload=request,
        response=response.raw_response,
        reservation=reservation,
        usage=response.normalized_usage if adapter.chat_completions else response.usage,
        cost=cost,
        latency_ms=latency_ms,
        status=response.status,
        raw_usage=response.raw_usage if adapter.chat_completions else None,
        normalized_usage=response.normalized_usage if adapter.chat_completions else None,
        finish_reason=response.finish_reason,
        rate_limit_headers=response.rate_limit_headers if adapter.chat_completions else None,
    )
    if response.status != "completed":
        raise ParaphraseError(f"model response status was {response.status}")
    return _response_text(response)


def paraphrase_claims(
    claims: Sequence[Mapping[str, Any]],
    *,
    output: str | Path = DEFAULT_OUTPUT,
    traces_dir: str | Path = DEFAULT_TRACES,
    ledger_path: str | Path = DEFAULT_LEDGER,
    provider: str = DEFAULT_PROVIDER,
    model: str | None = None,
    budget_usd: float = 2.0,
    sample_size: int = DEFAULT_SAMPLE,
    seed: int = DEFAULT_SEED,
    client: Any = None,
    dry_run: bool = False,
    prompt_path: str | Path = DEFAULT_PROMPT,
    max_output_tokens: int = DEFAULT_OUTPUT_TOKENS,
) -> list[dict[str, Any]]:
    """Paraphrase a seeded sample, retrying one constraint failure once."""

    from claimcheck.budget import BudgetExceeded, Ledger
    from claimcheck.providers import default_model, get_provider
    from claimcheck.trace import TraceRecorder, write_trace

    if dry_run and client is None:
        client = _DryRunChatClient()
    if client is None:
        raise ParaphraseError("a provider client is required unless dry_run=True")
    adapter = get_provider(provider)
    active_model = model or default_model(provider)
    ledger = Ledger(ledger_path, budget_usd=budget_usd, provider=provider)
    prompt = _prompt_text(prompt_path)
    selected = select_sample(claims, sample_size=sample_size, seed=seed)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path_dir = Path(traces_dir)
    trace_path_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(selected, 1):
        source_claim = str(source.get("claim") or "")
        recorder = TraceRecorder(source_claim, active_model, provider=provider)
        candidate = ""
        checks: list[dict[str, Any]] = []
        status = "rejected"
        error: dict[str, Any] | None = None
        for attempt in range(2):
            attempt_prompt = prompt
            if attempt:
                attempt_prompt += "\nYour previous rewrite failed these checks: " + "; ".join(checks[-1].get("reasons", [])) + ". Rewrite it again and preserve every required item."
            try:
                candidate = _request_once(
                    source_claim,
                    adapter=adapter,
                    client=client,
                    ledger=ledger,
                    recorder=recorder,
                    prompt=attempt_prompt,
                    model=active_model,
                    max_output_tokens=max_output_tokens,
                    provider=provider,
                )
                check = check_paraphrase_constraints(source_claim, candidate, spec=source.get("spec") if isinstance(source.get("spec"), Mapping) else None)
                check["attempt"] = attempt + 1
                checks.append(check)
                if check["accepted"]:
                    status = "accepted"
                    break
            except BudgetExceeded as exc:
                error = {"category": "budget_refused", "message": str(exc)}
                break
            except Exception as exc:
                error = {"category": type(exc).__name__, "message": str(exc)}
                break
        recorder.finish({"paraphrase": candidate, "status": status, "checks": checks})
        trace_path = write_trace(trace_path_dir, recorder)
        row = {
            "id": f"P{index:04d}",
            "paraphrase_of": source.get("id"),
            "layer": "paraphrased",
            "split": source.get("split"),
            "category": source.get("category"),
            "family": source.get("family", source.get("category")),
            "claim": candidate if candidate else source_claim,
            "spec": source.get("spec"),
            "gold_verdict": source.get("gold_verdict"),
            "gold_note": source.get("gold_note", ""),
            "source_facts": source.get("source_facts", []),
            "status": status,
            "checks": checks,
            "rejection_reasons": checks[-1].get("reasons", []) if checks and status != "accepted" else [],
            "trace_path": str(trace_path),
            "model": active_model,
            "provider": provider,
        }
        if error is not None:
            row["error"] = error
        rows.append(row)
    output_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return rows


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--traces-dir", type=Path, default=DEFAULT_TRACES)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    parser.add_argument("--model")
    parser.add_argument("--budget", type=float, default=2.0)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_OUTPUT_TOKENS)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        claims = load_jsonl(args.input)
        client = None
        model = args.model
        if not args.dry_run:
            from claimcheck.config import load_settings
            from claimcheck.providers import create_client

            settings = load_settings(read_key=True, provider=args.provider)
            if not settings.model_api_key:
                raise ParaphraseError(f"missing API key for provider {args.provider}")
            client = create_client(args.provider, settings.model_api_key)
            model = model or settings.model
        rows = paraphrase_claims(
            claims,
            output=args.output,
            traces_dir=args.traces_dir,
            ledger_path=args.ledger,
            provider=args.provider,
            model=model,
            client=client,
            budget_usd=args.budget,
            sample_size=args.sample_size,
            seed=args.seed,
            dry_run=args.dry_run,
            max_output_tokens=args.max_output_tokens,
        )
    except (OSError, ValueError, ParaphraseError) as exc:
        print(f"v2 paraphrase failed: {exc}", file=sys.stderr)
        return 1
    accepted = sum(row.get("status") == "accepted" for row in rows)
    print(json.dumps({"sampled": len(rows), "accepted": accepted, "rejected": len(rows) - accepted}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

