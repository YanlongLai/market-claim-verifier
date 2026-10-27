"""Offline-first single-shot versus tool-using evaluation runner and report."""

from __future__ import annotations

import json
import math
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .agent import (
    MAX_FINAL_OUTPUT_TOKENS,
    MAX_TOOL_OUTPUT_TOKENS,
    VERDICTS,
    _normalize_verdict,
    _response_text,
    _usage_dict,
    initial_request,
    verdict_text_format,
    verify_claim,
)
from .budget import BudgetExceeded, Ledger, UnknownModel
from .edgar import EdgarClient
from .trace import TraceRecorder, write_trace


SYSTEMS = ("single_shot", "agent")
DEFAULT_CLAIMS_PATH = Path("eval/claims.jsonl")
DEFAULT_MODEL = "muse-spark-1.3"
DEFAULT_BUDGET_USD = 2.00
DEFAULT_MAX_TURNS = 6
EVAL_VERDICTS = tuple(VERDICTS)
SPLITS = ("dev", "test")

SINGLE_SHOT_INSTRUCTIONS = """Judge the user's financial claim from your own knowledge.
Do not call tools and do not invent citations. Decompose the claim into every
atomic factual assertion, but use only what you already know. Today's date is
{today}. Return the same final verdict JSON schema as the verification agent:
verdict, summary, and sub_claims. For each sub-claim include all schema fields;
use claim_type other, an empty evidence_ids list, model_found_value null, and
insufficient_evidence when the assertion is not established by your knowledge.
The claim-level verdict is supported only when every factual part is supported;
any false part is contradicted; otherwise use insufficient_evidence."""


class EvaluationError(RuntimeError):
    """Raised for invalid evaluation inputs or report data."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _error_category(exc: BaseException) -> str:
    if isinstance(exc, BudgetExceeded):
        return "budget_refused"
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, ValueError):
        return "invalid_response"
    return "model_error"


def _jsonl(path: str | Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    source = Path(path)
    if not source.is_file():
        raise EvaluationError(f"claims JSONL not found: {source}")
    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvaluationError(f"invalid JSON on {source}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise EvaluationError(f"{source}:{line_number} is not a JSON object")
            result.append(value)
    return result


def validate_dataset(claims: Iterable[Mapping[str, Any]], *, strict: bool = True) -> None:
    """Validate the generated dataset without consulting a model or network."""

    items = list(claims)
    ids = [item.get("id") for item in items]
    if any(not isinstance(value, str) for value in ids) or len(set(ids)) != len(ids):
        raise EvaluationError("claim ids must be unique strings")
    for item in items:
        if item.get("split") not in SPLITS:
            raise EvaluationError(f"{item.get('id')}: invalid split")
        if item.get("gold_verdict") not in EVAL_VERDICTS:
            raise EvaluationError(f"{item.get('id')}: invalid gold verdict")
        if strict and (not isinstance(item.get("gold_note"), str) or not item["gold_note"].strip()):
            raise EvaluationError(f"{item.get('id')}: missing gold note")
        if not isinstance(item.get("claim"), str) or not item["claim"].strip():
            raise EvaluationError(f"{item.get('id')}: empty claim")
        if not isinstance(item.get("category"), str) or not item["category"].strip():
            raise EvaluationError(f"{item.get('id')}: missing category")
    if strict:
        if len(items) != 30:
            raise EvaluationError(f"expected 30 claims, found {len(items)}")
        expected_ids = [f"C{number:02d}" for number in range(1, 31)]
        if ids != expected_ids:
            raise EvaluationError(f"expected ids C01..C30 in order, found {ids}")
        counts = Counter(item.get("split") for item in items)
        if counts != Counter({"dev": 20, "test": 10}):
            raise EvaluationError(f"expected 20 dev and 10 test claims, found {dict(counts)}")
        required_categories = {
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
        missing = sorted(required_categories - {str(item["category"]) for item in items})
        if missing:
            raise EvaluationError(f"missing categories: {', '.join(missing)}")


def load_claims(path: str | Path = DEFAULT_CLAIMS_PATH, *, strict: bool = True) -> list[dict[str, Any]]:
    claims = _jsonl(path)
    validate_dataset(claims, strict=strict)
    return claims


def _configured_max_output_tokens(value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or value <= 0:
        raise EvaluationError("max_output_tokens must be a positive integer")
    return int(value)


def single_shot_request(
    claim: str,
    model: str,
    *,
    today: str | None = None,
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
) -> dict[str, Any]:
    """Return the one-call, no-tools Responses request used by single-shot."""

    configured = _configured_max_output_tokens(max_output_tokens)
    payload: dict[str, Any] = {
        "model": model,
        "instructions": SINGLE_SHOT_INSTRUCTIONS.format(
            today=today or datetime.now(timezone.utc).date().isoformat()
        ),
        "input": [{"role": "user", "content": claim}],
        "text": verdict_text_format(),
        "max_output_tokens": configured or MAX_FINAL_OUTPUT_TOKENS,
    }
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}
    return payload


def _call_single_shot(
    claim: str,
    *,
    client: Any,
    ledger: Ledger,
    model: str,
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
) -> dict[str, Any]:
    payload = single_shot_request(
        claim,
        model,
        max_output_tokens=max_output_tokens,
        reasoning_effort=reasoning_effort,
    )
    request_limit = int(payload["max_output_tokens"])
    reservation = ledger.reserve(
        payload,
        model=model,
        max_output_tokens=request_limit,
    )
    started = time.perf_counter()
    response = client.responses.create(**payload)
    latency_ms = (time.perf_counter() - started) * 1000
    cost = ledger.reconcile(reservation, _usage_dict(response))
    status = str(_get(response, "status") or "completed")
    if status != "completed":
        raise EvaluationError(f"single-shot response status was {status}")
    verdict = _normalize_verdict(_response_text(response))
    return {
        "verdict": verdict.get("verdict"),
        "summary": verdict.get("summary", ""),
        "sub_claims": verdict.get("sub_claims", []),
        "cost_usd": cost,
        "latency_ms": latency_ms,
        "model_output_invalid": bool(verdict.get("model_output_invalid")),
    }


def _offline_fetcher(url: str) -> bytes:
    raise RuntimeError(f"evaluation cache miss; network disabled for {url}")


def _pair_path(out_dir: Path, claim_id: str, system: str) -> Path:
    return out_dir / f"{claim_id}--{system}.json"


def _existing_pair(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    if value.get("status") in {"completed", "failed", "budget_stopped"}:
        return value
    return None


def _write_pair(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(dict(value), indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def _base_pair(claim: Mapping[str, Any], system: str, model: str) -> dict[str, Any]:
    return {
        "id": claim["id"],
        "split": claim["split"],
        "category": claim.get("category"),
        "claim": claim["claim"],
        "system": system,
        "model": model,
        "gold_verdict": claim["gold_verdict"],
        "status": "pending",
        "verdict": None,
        "summary": "",
        "sub_claims": [],
        "cost_usd": 0.0,
        "cost": 0.0,
        "latency_ms": 0.0,
        "latency": 0.0,
        "trace_path": None,
        "error": None,
    }


def _failure_pair(
    base: Mapping[str, Any],
    exc: BaseException,
    *,
    status: str = "failed",
) -> dict[str, Any]:
    value = dict(base)
    value.update(
        {
            "status": status,
            "error": {
                "category": _error_category(exc),
                "message": str(exc),
                "exception": type(exc).__name__,
            },
        }
    )
    return value


def run_evaluation(
    claims: Sequence[Mapping[str, Any]],
    *,
    systems: Sequence[str] = SYSTEMS,
    model: str = DEFAULT_MODEL,
    budget_usd: float = DEFAULT_BUDGET_USD,
    out_dir: str | Path,
    client: Any,
    edgar: EdgarClient | None = None,
    cache_dir: str | Path = ".cache",
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
    ledger_path: str | Path | None = None,
    secrets: Iterable[str] = (),
) -> dict[str, Any]:
    """Run selected systems sequentially, with resumable pair files."""

    systems = tuple(systems)
    if not systems or any(system not in SYSTEMS for system in systems):
        raise EvaluationError(f"systems must be a non-empty subset of {SYSTEMS}")
    if budget_usd < 0:
        raise EvaluationError("budget_usd must be non-negative")
    validate_dataset(claims, strict=False)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    traces = out / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    ledger_file = Path(ledger_path) if ledger_path is not None else out / "ledger.jsonl"
    ledger = Ledger(ledger_file, budget_usd=budget_usd)
    if edgar is None and "agent" in systems:
        edgar = EdgarClient(cache_dir, fetcher=_offline_fetcher)

    started_at = _now()
    skipped = 0
    executed = 0
    completed = 0
    failed = 0
    not_attempted = 0
    budget_stop: dict[str, Any] | None = None
    stop = False
    for claim in claims:
        for system in systems:
            path = _pair_path(out, str(claim["id"]), system)
            existing = _existing_pair(path)
            if existing is not None:
                skipped += 1
                continue
            if stop:
                break
            executed += 1
            base = _base_pair(claim, system, model)
            if system == "single_shot":
                try:
                    result = _call_single_shot(
                        str(claim["claim"]),
                        client=client,
                        ledger=ledger,
                        model=model,
                        max_output_tokens=max_output_tokens,
                        reasoning_effort=reasoning_effort,
                    )
                    base.update(
                        {
                            "status": "completed",
                            "verdict": result["verdict"],
                            "summary": result["summary"],
                            "sub_claims": result["sub_claims"],
                            "cost_usd": result["cost_usd"],
                            "cost": result["cost_usd"],
                            "latency_ms": result["latency_ms"],
                            "latency": result["latency_ms"],
                        }
                    )
                    if result.get("model_output_invalid"):
                        base["error"] = {
                            "category": "invalid_response",
                            "message": "model output was not valid structured verdict JSON",
                        }
                    completed += 1
                except BudgetExceeded as exc:
                    base = _failure_pair(base, exc, status="budget_stopped")
                    budget_stop = {
                        "id": claim["id"],
                        "system": system,
                        "message": str(exc),
                    }
                    stop = True
                except Exception as exc:  # one failed pair is recorded, never retried
                    base = _failure_pair(base, exc)
                    failed += 1
            else:
                if edgar is None:
                    raise EvaluationError("agent system needs an EdgarClient")
                recorder = TraceRecorder(str(claim["claim"]), model, secrets=secrets)
                started = time.perf_counter()
                try:
                    result = verify_claim(
                        str(claim["claim"]),
                        client,
                        edgar,
                        ledger,
                        model,
                        trace=recorder,
                        max_output_tokens=max_output_tokens,
                        reasoning_effort=reasoning_effort,
                    )
                    latency_ms = (time.perf_counter() - started) * 1000
                    trace_path = write_trace(traces, recorder)
                    relative_trace = str(trace_path.relative_to(out))
                    base.update(
                        {
                            "status": "completed",
                            "verdict": result.get("verdict"),
                            "summary": result.get("summary", ""),
                            "sub_claims": result.get("sub_claims", []),
                            "program_checks": result.get("program_checks", []),
                            "model_verdict": result.get("model_verdict"),
                            "cost_usd": recorder.total_cost,
                            "cost": recorder.total_cost,
                            "latency_ms": latency_ms,
                            "latency": latency_ms,
                            "trace_path": relative_trace,
                        }
                    )
                    completed += 1
                except BudgetExceeded as exc:
                    trace_path = write_trace(traces, recorder)
                    base = _failure_pair(base, exc, status="budget_stopped")
                    base["trace_path"] = str(trace_path.relative_to(out))
                    budget_stop = {
                        "id": claim["id"],
                        "system": system,
                        "message": str(exc),
                    }
                    stop = True
                except Exception as exc:  # one failed pair is recorded, never retried
                    trace_path = write_trace(traces, recorder)
                    base = _failure_pair(base, exc)
                    base["trace_path"] = str(trace_path.relative_to(out))
                    failed += 1
            _write_pair(path, base)
        if stop:
            break

    if stop:
        # Keep the pair-file contract total even when the hard budget stops a
        # sequential run before later claims are attempted.  These placeholders
        # contain no model result and are never retried automatically.
        for remaining_claim in claims:
            for remaining_system in systems:
                remaining_path = _pair_path(out, str(remaining_claim["id"]), remaining_system)
                if remaining_path.exists():
                    continue
                placeholder = _base_pair(remaining_claim, remaining_system, model)
                placeholder.update(
                    {
                        "status": "budget_stopped",
                        "error": {
                            "category": "budget_not_attempted",
                            "message": "run stopped after the shared budget was refused",
                        },
                    }
                )
                _write_pair(remaining_path, placeholder)
                not_attempted += 1

    manifest = {
        "started_at": started_at,
        "finished_at": _now(),
        "model": model,
        "budget_usd": budget_usd,
        "systems": list(systems),
        "claim_count": len(claims),
        "splits": sorted({str(claim.get("split")) for claim in claims}),
        "claim_ids": [str(claim["id"]) for claim in claims],
        "expected_pairs": len(claims) * len(systems),
        "executed_pairs": executed,
        "completed_pairs": completed,
        "failed_pairs": failed,
        "not_attempted_pairs": not_attempted,
        "skipped_pairs": skipped,
        "budget_stop": budget_stop,
        "ledger_path": str(ledger_file),
        "spent_total_usd": ledger.spent_total,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def _agent_final_payload(claim: str, model: str, max_output_tokens: int | None, reasoning_effort: str | None) -> dict[str, Any]:
    # This is a planning-only payload.  No request is made and no tool output
    # is fabricated; the reservation is explicitly labeled as an upper bound.
    payload: dict[str, Any] = {
        "model": model,
        "previous_response_id": "planning-response",
        "input": [{"role": "user", "content": "Return the final structured verdict now."}],
        "text": verdict_text_format(),
        "max_output_tokens": max_output_tokens or MAX_FINAL_OUTPUT_TOKENS,
    }
    if reasoning_effort:
        payload["reasoning"] = {"effort": reasoning_effort}
    return payload


def dry_run_plan(
    claims: Sequence[Mapping[str, Any]],
    *,
    systems: Sequence[str] = SYSTEMS,
    model: str = DEFAULT_MODEL,
    budget_usd: float = DEFAULT_BUDGET_USD,
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
    out_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Printable plan and conservative worst-case reservation, without calls."""

    systems = tuple(systems)
    validate_dataset(claims, strict=False)
    if budget_usd < 0:
        raise EvaluationError("budget_usd must be non-negative")
    ledger = Ledger(budget_usd=budget_usd, persist=False)
    single_amount = 0.0
    agent_amount = 0.0
    max_calls = 0
    for claim in claims:
        if "single_shot" in systems:
            payload = single_shot_request(
                str(claim["claim"]),
                model,
                max_output_tokens=max_output_tokens,
                reasoning_effort=reasoning_effort,
            )
            single_amount += ledger.estimate(
                payload,
                model=model,
                max_output_tokens=int(payload["max_output_tokens"]),
            ).amount
            max_calls += 1
        if "agent" in systems:
            initial = initial_request(
                str(claim["claim"]),
                model,
                max_output_tokens=max_output_tokens or MAX_TOOL_OUTPUT_TOKENS,
                reasoning_effort=reasoning_effort,
            )
            # Every tool turn may get one max-token retry.  A final structured
            # request may also get one retry.  The context sample makes the
            # estimate conservative without making a network call.
            context = {
                "response_id": "planning-response",
                "tool_outputs": [{"type": "function_call_output", "output": "x" * 4000}],
            }
            tool_limit = max_output_tokens or MAX_TOOL_OUTPUT_TOKENS
            final_limit = max_output_tokens or MAX_FINAL_OUTPUT_TOKENS
            for _ in range(DEFAULT_MAX_TURNS):
                agent_amount += ledger.estimate(
                    initial,
                    model=model,
                    max_output_tokens=tool_limit,
                    previous_context=context,
                ).amount
                agent_amount += ledger.estimate(
                    initial,
                    model=model,
                    max_output_tokens=tool_limit * 2,
                    previous_context=context,
                ).amount
            final = _agent_final_payload(str(claim["claim"]), model, final_limit, reasoning_effort)
            agent_amount += ledger.estimate(
                final,
                model=model,
                max_output_tokens=final_limit,
                previous_context=context,
            ).amount
            agent_amount += ledger.estimate(
                final,
                model=model,
                max_output_tokens=final_limit * 2,
                previous_context=context,
            ).amount
            max_calls += DEFAULT_MAX_TURNS * 2 + 2
    reservation = (single_amount if "single_shot" in systems else 0.0) + (agent_amount if "agent" in systems else 0.0)
    per_system = {}
    if "single_shot" in systems:
        per_system["single_shot"] = {
            "claims": len(claims),
            "max_model_calls": len(claims),
            "worst_case_reservation_usd": single_amount,
            "tools": False,
        }
    if "agent" in systems:
        per_system["agent"] = {
            "claims": len(claims),
            "max_model_calls": len(claims) * (DEFAULT_MAX_TURNS * 2 + 2),
            "worst_case_reservation_usd": agent_amount,
            "tools": True,
            "max_turns": DEFAULT_MAX_TURNS,
        }
    return {
        "claims": len(claims),
        "splits": sorted({str(claim.get("split")) for claim in claims}),
        "systems": list(systems),
        "model": model,
        "budget_usd": budget_usd,
        "out_dir": str(out_dir) if out_dir is not None else None,
        "max_model_calls": max_calls,
        "worst_case_reservation_usd": reservation,
        "budget_would_be_exceeded": reservation > budget_usd,
        "note": "Conservative upper bound: six tool turns and one max-token retry per turn, plus a retried final request for each agent claim; no model or network call is made.",
        "per_system": per_system,
    }


def _percentile(values: Sequence[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile / 100.0
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def compute_metrics(
    claims: Sequence[Mapping[str, Any]],
    results: Sequence[Mapping[str, Any]],
    *,
    system: str,
    split: str,
) -> dict[str, Any]:
    """Compute one system/split metric block; kept pure for offline tests."""

    expected = [claim for claim in claims if claim.get("split") == split]
    by_id = {
        str(result.get("id")): result
        for result in results
        if result.get("system") == system and result.get("split") == split
    }
    predicted: dict[str, str] = {}
    latencies: list[float] = []
    costs: list[float] = []
    errors: list[dict[str, Any]] = []
    for claim in expected:
        result = by_id.get(str(claim["id"]))
        if result is None:
            errors.append({"id": claim["id"], "category": "missing_result", "message": "no pair result"})
            continue
        verdict = result.get("verdict")
        if result.get("status") == "completed" and verdict in EVAL_VERDICTS:
            predicted[str(claim["id"])] = str(verdict)
            try:
                latencies.append(float(result.get("latency_ms", 0.0)))
            except (TypeError, ValueError):
                pass
            try:
                costs.append(float(result.get("cost_usd", 0.0)))
            except (TypeError, ValueError):
                pass
        else:
            error = result.get("error")
            if isinstance(error, Mapping):
                errors.append(
                    {
                        "id": claim["id"],
                        "category": error.get("category", "failed"),
                        "message": error.get("message", ""),
                        "status": result.get("status"),
                    }
                )
            else:
                errors.append({"id": claim["id"], "category": "failed", "message": "no verdict"})

    correct = sum(
        predicted.get(str(claim["id"])) == claim.get("gold_verdict")
        for claim in expected
    )
    class_metrics: dict[str, dict[str, Any]] = {}
    for gold_class in EVAL_VERDICTS:
        support = sum(claim.get("gold_verdict") == gold_class for claim in expected)
        true_positive = sum(
            claim.get("gold_verdict") == gold_class
            and predicted.get(str(claim["id"])) == gold_class
            for claim in expected
        )
        predicted_count = sum(value == gold_class for value in predicted.values())
        class_metrics[gold_class] = {
            "support": support,
            "predicted": predicted_count,
            "true_positive": true_positive,
            "precision": true_positive / predicted_count if predicted_count else 0.0,
            "recall": true_positive / support if support else 0.0,
        }
    harmful_gold = sum(
        claim.get("gold_verdict") in {"contradicted", "insufficient_evidence"}
        for claim in expected
    )
    false_supported = sum(
        predicted.get(str(claim["id"])) == "supported"
        and claim.get("gold_verdict") in {"contradicted", "insufficient_evidence"}
        for claim in expected
    )
    return {
        "system": system,
        "split": split,
        "n_claims": len(expected),
        "n_completed": len(predicted),
        "n_errors": len(errors),
        "accuracy": correct / len(expected) if expected else 0.0,
        "correct": correct,
        "per_gold_class": class_metrics,
        "false_supported_rate": false_supported / harmful_gold if harmful_gold else 0.0,
        "false_supported": false_supported,
        "harmful_gold": harmful_gold,
        "insufficient_rate": sum(value == "insufficient_evidence" for value in predicted.values()) / len(expected) if expected else 0.0,
        "latency_ms": {
            "mean": sum(latencies) / len(latencies) if latencies else None,
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
        },
        "cost_usd": {
            "total": sum(costs),
            "mean": sum(costs) / len(costs) if costs else None,
        },
        "errors": errors,
    }


def _load_result_files(out_dir: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted(out_dir.glob("*.json")):
        if path.name in {"manifest.json", "summary.json"}:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and value.get("id") and value.get("system"):
            results.append(value)
    return results


def _md_cell(value: Any) -> str:
    return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ")


def _fmt_metric(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value)


def _write_report(path: Path, summary: Mapping[str, Any], claims: Sequence[Mapping[str, Any]], results: Sequence[Mapping[str, Any]]) -> None:
    lines = [
        "# Market claim evaluation report",
        "",
        f"Generated: {summary.get('generated_at', '—')}",
        "",
        "Accuracy uses all expected claims in the denominator; a missing, failed, or budget-stopped pair is not a correct prediction. Per-class recall uses all claims of that gold class, while precision uses completed predictions of that class. False-supported rate is the harmful error rate among gold contradicted or insufficient-evidence claims. Latency and cost summaries use completed pairs only.",
        "",
        "No significance claims are made: each split is small (20 dev and 10 test claims).",
        "",
        "## Metrics",
        "",
        "| System | Split | n | completed | errors | accuracy | false-supported rate | insufficient rate | mean latency ms | p50 ms | p95 ms | total cost | mean cost |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    metrics = summary.get("metrics", {})
    for system in SYSTEMS:
        for split in SPLITS:
            metric = metrics.get(system, {}).get(split)
            if not isinstance(metric, Mapping):
                continue
            latency = metric.get("latency_ms", {})
            cost = metric.get("cost_usd", {})
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(system),
                        _md_cell(split),
                        _md_cell(metric.get("n_claims")),
                        _md_cell(metric.get("n_completed")),
                        _md_cell(metric.get("n_errors")),
                        _fmt_metric(metric.get("accuracy")),
                        _fmt_metric(metric.get("false_supported_rate")),
                        _fmt_metric(metric.get("insufficient_rate")),
                        _fmt_metric(latency.get("mean"), 1),
                        _fmt_metric(latency.get("p50"), 1),
                        _fmt_metric(latency.get("p95"), 1),
                        _fmt_metric(cost.get("total"), 6),
                        _fmt_metric(cost.get("mean"), 6),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "### Per-gold-class precision and recall",
            "",
            "| System | Split | Gold class | Support | Predicted | Precision | Recall |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for system in SYSTEMS:
        for split in SPLITS:
            metric = metrics.get(system, {}).get(split, {})
            for gold_class in EVAL_VERDICTS:
                item = metric.get("per_gold_class", {}).get(gold_class, {})
                lines.append(
                    f"| {system} | {split} | {gold_class} | {item.get('support', 0)} | {item.get('predicted', 0)} | {_fmt_metric(item.get('precision', 0.0))} | {_fmt_metric(item.get('recall', 0.0))} |"
                )
    lines.extend(
        [
            "",
            "## Per-claim results",
            "",
            "| ID | Split | Category | Claim | Gold | Single-shot | Agent |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    by_pair = {(str(result.get("id")), str(result.get("system"))): result for result in results}
    for claim in claims:
        values: dict[str, str] = {}
        for system in SYSTEMS:
            result = by_pair.get((str(claim["id"]), system))
            if result is None:
                values[system] = "missing"
            elif result.get("status") == "completed":
                values[system] = str(result.get("verdict") or "invalid")
            else:
                error = result.get("error") if isinstance(result.get("error"), Mapping) else {}
                values[system] = f"{result.get('status', 'failed')}: {error.get('category', 'error')}"
        lines.append(
            f"| {claim['id']} | {claim['split']} | {_md_cell(claim.get('category'))} | {_md_cell(claim.get('claim'))} | {claim.get('gold_verdict')} | {values.get('single_shot', '—')} | {values.get('agent', '—')} |"
        )
    lines.extend(["", "## Agent errors", ""])
    agent_errors = summary.get("agent_errors", [])
    if agent_errors:
        lines.extend(
            [
                "| ID | Split | Category | Status | Message |",
                "|---|---|---|---|---|",
            ]
        )
        claim_by_id = {str(claim["id"]): claim for claim in claims}
        for error in agent_errors:
            claim = claim_by_id.get(str(error.get("id")), {})
            lines.append(
                f"| {error.get('id')} | {claim.get('split', '—')} | {error.get('category', '—')} | {error.get('status', '—')} | {_md_cell(error.get('message', ''))} |"
            )
    else:
        lines.append("None recorded.")
    lines.extend(
        [
            "",
            "## Accounting",
            "",
            f"Budget stop: {summary.get('manifest', {}).get('budget_stop') or 'none recorded'}.",
            f"Total ledger spend/reservations reported by the run: ${float(summary.get('manifest', {}).get('spent_total_usd', 0.0)):.6f}.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def report_evaluation(
    out_dir: str | Path,
    *,
    claims_path: str | Path = DEFAULT_CLAIMS_PATH,
) -> dict[str, Any]:
    out = Path(out_dir)
    claims = load_claims(claims_path, strict=False)
    results = _load_result_files(out)
    manifest: dict[str, Any] = {}
    manifest_path = out / "manifest.json"
    if manifest_path.is_file():
        try:
            value = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                manifest = value
        except (OSError, json.JSONDecodeError):
            pass
    claim_ids = manifest.get("claim_ids")
    if isinstance(claim_ids, list) and claim_ids:
        selected_ids = {str(value) for value in claim_ids}
        claims = [claim for claim in claims if str(claim.get("id")) in selected_ids]
    metrics: dict[str, dict[str, Any]] = defaultdict(dict)
    for system in SYSTEMS:
        for split in SPLITS:
            metrics[system][split] = compute_metrics(claims, results, system=system, split=split)
    agent_errors = [
        error
        for split_metrics in metrics.get("agent", {}).values()
        for error in split_metrics.get("errors", [])
    ]
    summary: dict[str, Any] = {
        "generated_at": _now(),
        "out_dir": str(out),
        "manifest": manifest,
        "metrics": {system: dict(split_metrics) for system, split_metrics in metrics.items()},
        "agent_errors": agent_errors,
        "result_count": len(results),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    _write_report(out / "REPORT.md", summary, claims, results)
    return summary


__all__ = [
    "DEFAULT_BUDGET_USD",
    "DEFAULT_CLAIMS_PATH",
    "DEFAULT_MODEL",
    "EvaluationError",
    "SYSTEMS",
    "compute_metrics",
    "dry_run_plan",
    "load_claims",
    "report_evaluation",
    "run_evaluation",
    "single_shot_request",
    "validate_dataset",
]
