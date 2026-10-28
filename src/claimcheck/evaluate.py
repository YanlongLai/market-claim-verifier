"""Offline-first single-shot versus tool-using evaluation runner and report."""

from __future__ import annotations

import json
import hashlib
import importlib.metadata
import math
import platform
import subprocess
import time
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .agent import (
    MAX_FINAL_OUTPUT_TOKENS,
    MAX_TOOL_OUTPUT_TOKENS,
    VERDICTS,
    _normalize_verdict,
    _invalid_model_json_result,
    _parse_strict_verdict,
    _response_text,
    _request_with_retry,
    initial_request,
    verdict_text_format,
    verify_claim,
)
from .budget import BudgetExceeded, Ledger, UnknownModel
from .edgar import EdgarClient
from .prompts import prompt_registry, prompt_versions_for
from .providers import (
    META_PROVIDER,
    PROVIDERS,
    ProviderAdapter,
    canonical_system,
    default_model,
    get_provider,
    system_parts,
)
from .trace import TraceRecorder, usage_tokens, write_trace


SYSTEMS = (
    "single_shot@meta",
    "agent@meta",
    "single_shot@baseten",
    "agent@baseten",
    "single_shot@fireworks",
    "agent@fireworks",
)
LEGACY_SYSTEMS = ("single_shot", "agent")
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
    provider: str | ProviderAdapter = META_PROVIDER,
) -> dict[str, Any]:
    """Return the one-call, no-tools Responses request used by single-shot."""

    configured = _configured_max_output_tokens(max_output_tokens)
    active_provider = get_provider(provider)
    if active_provider.name != META_PROVIDER:
        return active_provider.single_shot_request(
            claim,
            model,
            today=today or datetime.now(timezone.utc).date().isoformat(),
            max_output_tokens=configured or MAX_FINAL_OUTPUT_TOKENS,
            reasoning_effort=reasoning_effort,
        )
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
    recorder: TraceRecorder | None = None,
    today: str | None = None,
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
    provider: str | ProviderAdapter = META_PROVIDER,
) -> dict[str, Any]:
    active_provider = get_provider(provider)
    if recorder is None:
        recorder = TraceRecorder(claim, model, provider=active_provider.name)
    configured = _configured_max_output_tokens(max_output_tokens)
    request_limit = configured or MAX_FINAL_OUTPUT_TOKENS
    payload = active_provider.single_shot_request(
        claim,
        model,
        today=today or datetime.now(timezone.utc).date().isoformat(),
        max_output_tokens=request_limit,
        reasoning_effort=reasoning_effort,
    )
    response, completed = _request_with_retry(
        client=client,
        ledger=ledger,
        recorder=recorder,
        payload=payload,
        model=model,
        provider=active_provider,
        max_output_tokens=request_limit,
        previous_context=None,
        turn=1,
        phase="single_shot",
    )
    if not completed:
        raise EvaluationError(f"single-shot response status was {response.status}")
    if active_provider.chat_completions:
        verdict = _parse_strict_verdict(_response_text(response))
        if verdict is None:
            repair_payload = active_provider.repair_request(
                payload,
                response,
                model=model,
                max_output_tokens=request_limit,
                reasoning_effort=reasoning_effort,
            )
            repaired, repair_completed = _request_with_retry(
                client=client,
                ledger=ledger,
                recorder=recorder,
                payload=repair_payload,
                model=model,
                provider=active_provider,
                max_output_tokens=request_limit,
                previous_context=None,
                turn=2,
                phase="single_shot_repair",
                retry_incomplete=False,
            )
            if not repair_completed:
                result = _invalid_model_json_result(recorder)
                result.update({"cost_usd": recorder.total_cost, "latency_ms": recorder.total_latency_ms})
                return result
            verdict = _parse_strict_verdict(_response_text(repaired))
            if verdict is None:
                result = _invalid_model_json_result(recorder)
                result.update({"cost_usd": recorder.total_cost, "latency_ms": recorder.total_latency_ms})
                return result
        else:
            repaired = None
    else:
        verdict = _normalize_verdict(_response_text(response))
    recorder.finish(verdict)
    return {
        "verdict": verdict.get("verdict"),
        "summary": verdict.get("summary", ""),
        "sub_claims": verdict.get("sub_claims", []),
        "cost_usd": recorder.total_cost,
        "latency_ms": recorder.total_latency_ms,
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
    required_recording_fields = {
        "prompt_versions",
        "tokens",
        "model_calls",
        "tool_calls",
        "started_at",
        "finished_at",
    }
    if value.get("status") in {"completed", "failed", "budget_stopped"} and required_recording_fields <= set(value):
        return value
    return None


def _write_pair(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(dict(value), indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def _zero_tokens() -> dict[str, int]:
    return {"input": 0, "cached": 0, "output": 0, "reasoning": 0}


def _add_tokens(target: dict[str, int], value: Any) -> None:
    if isinstance(value, Mapping) and any(key in value for key in target):
        normalized: dict[str, int] = {}
        for key in target:
            raw = value.get(key, 0)
            try:
                normalized[key] = max(0, int(raw or 0)) if not isinstance(raw, bool) else 0
            except (TypeError, ValueError):
                normalized[key] = 0
    else:
        normalized = usage_tokens(value)
    for key in target:
        target[key] += normalized.get(key, 0)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str | None:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError:
        return None


def _git_metadata() -> dict[str, Any]:
    """Capture local repository identity without invoking any network command."""

    repo_root = Path(__file__).resolve().parents[2]

    def run(*arguments: str) -> str | None:
        try:
            completed = subprocess.run(
                ["git", *arguments],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return None
        return completed.stdout.strip()

    commit = run("rev-parse", "HEAD")
    dirty_listing = run("status", "--porcelain", "--untracked-files=all")
    return {
        "commit": commit,
        "dirty": bool(dirty_listing),
    }


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _version_metadata() -> dict[str, Any]:
    python_version = platform.python_version()
    openai_version = _package_version("openai")
    return {
        "python": python_version,
        "openai": openai_version,
        "python_version": python_version,
        "openai_version": openai_version,
    }


def _claims_digest(
    claims: Sequence[Mapping[str, Any]],
    claims_path: str | Path | None,
) -> tuple[str | None, str | None]:
    if claims_path is not None:
        path = Path(claims_path)
        return str(path), _sha256_file(path)
    default_path = DEFAULT_CLAIMS_PATH
    if default_path.is_file():
        return str(default_path), _sha256_file(default_path)
    # Direct library callers may provide an in-memory fixture.  Preserve a
    # reproducible JSONL digest even though there is no source file to name.
    serialized = "".join(
        json.dumps(dict(claim), ensure_ascii=False, separators=(",", ":")) + "\n"
        for claim in claims
    ).encode("utf-8")
    return None, _sha256_bytes(serialized)


def _snapshot_hashes(edgar: Any) -> dict[str, str]:
    getter_or_value = getattr(edgar, "companyfacts_snapshot_hashes", None)
    if callable(getter_or_value):
        value = getter_or_value()
    else:
        value = getter_or_value
    if isinstance(value, Mapping):
        return {str(key): str(item) for key, item in value.items()}
    cache = getattr(edgar, "_document_cache", None)
    if not isinstance(cache, Mapping):
        return {}
    snapshots: dict[str, str] = {}
    for filename, document_and_hash in cache.items():
        if not str(filename).startswith("companyfacts-"):
            continue
        if isinstance(document_and_hash, (tuple, list)) and len(document_and_hash) >= 2:
            digest = document_and_hash[1]
            if digest:
                snapshots[str(filename)] = str(digest)
    return snapshots


def _prompt_registry_manifest() -> dict[str, dict[str, str]]:
    return {
        name: {
            "text": entry["text"],
            "sha256": entry["sha256"],
            "file": entry["file"],
        }
        for name, entry in prompt_registry().items()
    }


def _base_pair(
    claim: Mapping[str, Any],
    system: str,
    model: str,
    *,
    prompt_versions: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "id": claim["id"],
        "split": claim["split"],
        "category": claim.get("category"),
        "claim": claim["claim"],
        "system": canonical_system(system),
        "method": system_parts(system)[0],
        "provider": system_parts(system)[1],
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
        "prompt_versions": dict(prompt_versions),
        "tokens": _zero_tokens(),
        "model_calls": 0,
        "tool_calls": 0,
        "started_at": _now(),
        "finished_at": None,
        "error": None,
    }


def _model_for(model: str | None, provider: str) -> str:
    return model or default_model(provider)


def _client_for(client: Any, provider: str) -> Any:
    if isinstance(client, Mapping):
        try:
            return client[provider]
        except KeyError as exc:
            raise EvaluationError(f"missing client for provider {provider}") from exc
    return client


def _secrets_for(secrets: Any, provider: str) -> Iterable[str]:
    if isinstance(secrets, Mapping):
        value = secrets.get(provider, ())
        return value if isinstance(value, Iterable) and not isinstance(value, (str, bytes)) else (str(value),)
    return secrets


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


def _aggregate_result_observations(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    totals: dict[str, Any] = {
        "pairs": 0,
        "cost_usd": 0.0,
        "tokens": _zero_tokens(),
        "model_calls": 0,
        "tool_calls": 0,
    }
    per_system: dict[str, dict[str, Any]] = {}
    for result in results:
        raw_system = str(result.get("system") or "")
        if not raw_system:
            continue
        try:
            system = canonical_system(raw_system)
        except ValueError:
            system = raw_system
        bucket = per_system.setdefault(
            system,
            {
                "pairs": 0,
                "cost_usd": 0.0,
                "tokens": _zero_tokens(),
                "model_calls": 0,
                "tool_calls": 0,
            },
        )
        bucket["pairs"] += 1
        totals["pairs"] += 1
        try:
            cost = float(result.get("cost_usd", 0.0) or 0.0)
        except (TypeError, ValueError):
            cost = 0.0
        bucket["cost_usd"] += cost
        totals["cost_usd"] += cost
        _add_tokens(bucket["tokens"], result.get("tokens"))
        _add_tokens(totals["tokens"], result.get("tokens"))
        for key in ("model_calls", "tool_calls"):
            try:
                calls = max(0, int(result.get(key, 0) or 0))
            except (TypeError, ValueError):
                calls = 0
            bucket[key] += calls
            totals[key] += calls
    return {**totals, "per_system": per_system}


def _write_manifest(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(dict(value), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def run_evaluation(
    claims: Sequence[Mapping[str, Any]],
    *,
    systems: Sequence[str] = SYSTEMS,
    model: str | None = None,
    budget_usd: float = DEFAULT_BUDGET_USD,
    out_dir: str | Path,
    client: Any,
    edgar: EdgarClient | None = None,
    cache_dir: str | Path = ".cache",
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
    ledger_path: str | Path | None = None,
    secrets: Iterable[str] = (),
    split: str | None = None,
    cli_args: Sequence[str] | None = None,
    claims_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run selected systems sequentially, with resumable pair files and evidence manifests."""

    systems = tuple(str(system).strip() for system in systems)
    if not systems:
        raise EvaluationError(f"systems must be a non-empty subset of {SYSTEMS}")
    system_info: dict[str, tuple[str, str]] = {}
    canonical_names: set[str] = set()
    for system in systems:
        if system not in SYSTEMS and system not in LEGACY_SYSTEMS:
            raise EvaluationError(
                f"systems must be a non-empty subset of {SYSTEMS} (legacy aliases: {LEGACY_SYSTEMS})"
            )
        try:
            parts = system_parts(system)
        except ValueError as exc:
            raise EvaluationError(str(exc)) from exc
        canonical_name = canonical_system(system)
        if canonical_name in canonical_names:
            raise EvaluationError("systems must not contain duplicate methods/providers")
        canonical_names.add(canonical_name)
        system_info[system] = parts
    if budget_usd < 0:
        raise EvaluationError("budget_usd must be non-negative")
    validate_dataset(claims, strict=False)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    traces = out / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    ledger_file = Path(ledger_path) if ledger_path is not None else out / "ledger.jsonl"
    ledger = Ledger(
        ledger_file,
        budget_usd=budget_usd,
        provider_budgets={
            provider: budget_usd for _, provider in system_info.values()
        },
    )
    if edgar is None and any(method == "agent" for method, _ in system_info.values()):
        edgar = EdgarClient(cache_dir, fetcher=_offline_fetcher)

    existing_manifest: dict[str, Any] = {}
    manifest_path = out / "manifest.json"
    if manifest_path.is_file():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing_manifest = loaded
        except (OSError, json.JSONDecodeError):
            existing_manifest = {}

    invocation_started = time.perf_counter()
    started_at = str(existing_manifest.get("started_at") or _now())
    run_id = str(existing_manifest.get("run_id") or f"eval-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}")
    split_value = split or (
        "all"
        if len({str(claim.get("split")) for claim in claims}) != 1
        else str(next(iter(claims), {}).get("split", "all"))
    )
    claims_source, claims_digest = _claims_digest(claims, claims_path)
    prompt_manifest = _prompt_registry_manifest()
    prompt_versions = {system: prompt_versions_for(system) for system in systems}
    ledger_before = ledger.spent_total
    git = _git_metadata()
    versions = _version_metadata()
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "status": "running",
        "started_at": started_at,
        "finished_at": None,
        "wall_clock_s": None,
        "git_commit": git["commit"],
        "git_dirty": git["dirty"],
        "git": git,
        "python_version": versions["python_version"],
        "openai_version": versions["openai_version"],
        "versions": versions,
        "model": model
        or (
            default_model(next(iter({provider for _, provider in system_info.values()})))
            if len({provider for _, provider in system_info.values()}) == 1
            else "mixed"
        ),
        "models": {
            system: model or default_model(provider)
            for system, (_, provider) in system_info.items()
        },
        "systems": [canonical_system(system) for system in systems],
        "split": split_value,
        "splits": sorted({str(claim.get("split")) for claim in claims}),
        "cli_args": list(cli_args or []),
        "budget_usd": budget_usd,
        "budget": {
            "usd": budget_usd,
            "per_provider_usd": {
                provider: budget_usd for _, provider in system_info.values()
            },
        },
        "ledger_path": str(ledger_file),
        "ledger_spend_before_usd": ledger_before,
        "ledger_spend_after_usd": ledger_before,
        "ledger_spend": {"before_usd": ledger_before, "after_usd": ledger_before},
        "claims_jsonl_path": claims_source,
        "claims_jsonl_sha256": claims_digest,
        "sec_companyfacts_snapshot_sha256": {},
        "prompt_registry": prompt_manifest,
        "claim_count": len(claims),
        "claim_ids": [str(claim["id"]) for claim in claims],
        "expected_pairs": len(claims) * len(systems),
        "executed_pairs": 0,
        "completed_pairs": 0,
        "failed_pairs": 0,
        "not_attempted_pairs": 0,
        "skipped_pairs": 0,
        "budget_stop": None,
        "totals": {
            "pairs": 0,
            "cost_usd": 0.0,
            "tokens": _zero_tokens(),
            "model_calls": 0,
            "tool_calls": 0,
            "per_system": {},
        },
    }
    _write_manifest(manifest_path, manifest)

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
            method, provider_name = system_info[system]
            pair_model = _model_for(model, provider_name)
            pair_client = _client_for(client, provider_name)
            pair_secrets = _secrets_for(secrets, provider_name)
            base = _base_pair(
                claim,
                system,
                pair_model,
                prompt_versions=prompt_versions[system],
            )
            pair_started = time.perf_counter()
            trace_path: Path | None = None
            if method == "single_shot":
                recorder = TraceRecorder(
                    str(claim["claim"]), pair_model, provider=provider_name, secrets=pair_secrets
                )
                try:
                    result = _call_single_shot(
                        str(claim["claim"]),
                        client=pair_client,
                        ledger=ledger,
                        model=pair_model,
                        recorder=recorder,
                        today=started_at[:10],
                        max_output_tokens=max_output_tokens,
                        reasoning_effort=reasoning_effort,
                        provider=provider_name,
                    )
                    pair_latency_ms = (time.perf_counter() - pair_started) * 1000
                    summary = recorder.summary()
                    trace_path = write_trace(traces, recorder)
                    base.update(
                        {
                            "status": "completed",
                            "verdict": result["verdict"],
                            "summary": result["summary"],
                            "sub_claims": result["sub_claims"],
                            "cost_usd": result["cost_usd"],
                            "cost": result["cost_usd"],
                            "latency_ms": pair_latency_ms,
                            "latency": pair_latency_ms,
                            "tokens": summary["tokens"],
                            "model_calls": summary["model_calls"],
                            "tool_calls": summary["tool_calls"],
                            "trace_path": str(trace_path.relative_to(out)),
                        }
                    )
                    if result.get("model_output_invalid"):
                        base["error"] = {
                            "category": "invalid_response",
                            "message": "model output was not valid structured verdict JSON",
                        }
                    if result.get("invalid_model_json"):
                        base["error"] = {
                            "category": "invalid_model_json",
                            "message": "model output was invalid twice, including the repair request",
                        }
                    completed += 1
                except BudgetExceeded as exc:
                    base = _failure_pair(base, exc, status="budget_stopped")
                    budget_stop = {
                        "id": claim["id"],
                        "system": canonical_system(system),
                        "message": str(exc),
                    }
                    stop = True
                except Exception as exc:  # one failed pair is recorded, never retried
                    base = _failure_pair(base, exc)
                    failed += 1
                finally:
                    if trace_path is None:
                        trace_path = write_trace(traces, recorder)
                    base["trace_path"] = str(trace_path.relative_to(out))
                    base["finished_at"] = _now()
                    base["latency_ms"] = base.get("latency_ms") or (time.perf_counter() - pair_started) * 1000
                    base["latency"] = base["latency_ms"]
                    summary = recorder.summary()
                    base["cost_usd"] = summary["cost_usd"]
                    base["cost"] = summary["cost_usd"]
                    base["tokens"] = summary["tokens"]
                    base["model_calls"] = summary["model_calls"]
                    base["tool_calls"] = summary["tool_calls"]
            else:
                if edgar is None:
                    raise EvaluationError("agent system needs an EdgarClient")
                recorder = TraceRecorder(
                    str(claim["claim"]), pair_model, provider=provider_name, secrets=pair_secrets
                )
                try:
                    result = verify_claim(
                        str(claim["claim"]),
                        pair_client,
                        edgar,
                        ledger,
                        pair_model,
                        trace=recorder,
                        max_output_tokens=max_output_tokens,
                        reasoning_effort=reasoning_effort,
                        provider=provider_name,
                    )
                    pair_latency_ms = (time.perf_counter() - pair_started) * 1000
                    summary = recorder.summary()
                    trace_path = write_trace(traces, recorder)
                    base.update(
                        {
                            "status": "completed",
                            "verdict": result.get("verdict"),
                            "summary": result.get("summary", ""),
                            "sub_claims": result.get("sub_claims", []),
                            "program_checks": result.get("program_checks", []),
                            "model_verdict": result.get("model_verdict"),
                            "cost_usd": summary["cost_usd"],
                            "cost": summary["cost_usd"],
                            "latency_ms": pair_latency_ms,
                            "latency": pair_latency_ms,
                            "tokens": summary["tokens"],
                            "model_calls": summary["model_calls"],
                            "tool_calls": summary["tool_calls"],
                            "trace_path": str(trace_path.relative_to(out)),
                        }
                    )
                    completed += 1
                except BudgetExceeded as exc:
                    base = _failure_pair(base, exc, status="budget_stopped")
                    budget_stop = {
                        "id": claim["id"],
                        "system": canonical_system(system),
                        "message": str(exc),
                    }
                    stop = True
                except Exception as exc:  # one failed pair is recorded, never retried
                    base = _failure_pair(base, exc)
                    failed += 1
                finally:
                    if trace_path is None:
                        trace_path = write_trace(traces, recorder)
                    base["trace_path"] = str(trace_path.relative_to(out))
                    base["finished_at"] = _now()
                    base["latency_ms"] = base.get("latency_ms") or (time.perf_counter() - pair_started) * 1000
                    base["latency"] = base["latency_ms"]
                    summary = recorder.summary()
                    base["cost_usd"] = summary["cost_usd"]
                    base["cost"] = summary["cost_usd"]
                    base["tokens"] = summary["tokens"]
                    base["model_calls"] = summary["model_calls"]
                    base["tool_calls"] = summary["tool_calls"]
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
                placeholder = _base_pair(
                    remaining_claim,
                    remaining_system,
                    model,
                    prompt_versions=prompt_versions[remaining_system],
                )
                placeholder.update(
                    {
                        "status": "budget_stopped",
                        "error": {
                            "category": "budget_not_attempted",
                            "message": "run stopped after the shared budget was refused",
                        },
                        "finished_at": _now(),
                    }
                )
                _write_pair(remaining_path, placeholder)
                not_attempted += 1

    result_records = _load_result_files(out)
    observations = _aggregate_result_observations(result_records)
    finished_at = _now()
    ledger_after = ledger.spent_total
    previous_snapshots = existing_manifest.get("sec_companyfacts_snapshot_sha256", {})
    if not isinstance(previous_snapshots, Mapping):
        previous_snapshots = {}
    snapshots = {
        str(key): str(value)
        for key, value in previous_snapshots.items()
    }
    snapshots.update(_snapshot_hashes(edgar))
    manifest.update(
        {
            "status": "completed",
            "finished_at": finished_at,
            "wall_clock_s": round(time.perf_counter() - invocation_started, 6),
            "executed_pairs": executed,
            "completed_pairs": completed,
            "failed_pairs": failed,
            "not_attempted_pairs": not_attempted,
            "skipped_pairs": skipped,
            "budget_stop": budget_stop,
            "ledger_spend_after_usd": ledger_after,
            "ledger_spend_after_by_provider_usd": {
                provider: ledger.spent_for_provider(provider)
                for _, provider in system_info.values()
            },
            "ledger_spend": {"before_usd": ledger_before, "after_usd": ledger_after},
            "sec_companyfacts_snapshot_sha256": snapshots,
            "totals": observations,
        }
    )
    _write_manifest(manifest_path, manifest)
    return manifest


def _agent_final_payload(
    claim: str,
    model: str,
    max_output_tokens: int | None,
    reasoning_effort: str | None,
    provider: str | ProviderAdapter = META_PROVIDER,
) -> dict[str, Any]:
    # This is a planning-only payload.  No request is made and no tool output
    # is fabricated; the reservation is explicitly labeled as an upper bound.
    active_provider = get_provider(provider)
    if active_provider.chat_completions:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": active_provider.tool_loop_instructions()},
                {"role": "user", "content": claim},
                {"role": "assistant", "content": None},
                {"role": "user", "content": active_provider.final_verdict_prompt()},
            ],
            "max_tokens": max_output_tokens or MAX_FINAL_OUTPUT_TOKENS,
        }
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort
        return payload
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
    model: str | None = None,
    budget_usd: float = DEFAULT_BUDGET_USD,
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
    out_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Printable plan and conservative worst-case reservation, without calls."""

    systems = tuple(str(system).strip() for system in systems)
    if not systems:
        raise EvaluationError(f"systems must be a non-empty subset of {SYSTEMS}")
    system_info: dict[str, tuple[str, str]] = {}
    seen: set[str] = set()
    for system in systems:
        if system not in SYSTEMS and system not in LEGACY_SYSTEMS:
            raise EvaluationError(f"systems must be a non-empty subset of {SYSTEMS}")
        system_info[system] = system_parts(system)
        canonical_name = canonical_system(system)
        if canonical_name in seen:
            raise EvaluationError("systems must not contain duplicate methods/providers")
        seen.add(canonical_name)
    validate_dataset(claims, strict=False)
    if budget_usd < 0:
        raise EvaluationError("budget_usd must be non-negative")
    ledger = Ledger(budget_usd=budget_usd, persist=False)
    per_system_amount: dict[str, float] = {system: 0.0 for system in systems}
    per_provider_amount: dict[str, float] = {provider: 0.0 for _, provider in system_info.values()}
    max_calls = 0
    for claim in claims:
        for system in systems:
            method, provider_name = system_info[system]
            pair_model = _model_for(model, provider_name)
            active_provider = get_provider(provider_name)
            if method == "single_shot":
                payload = single_shot_request(
                    str(claim["claim"]),
                    pair_model,
                    max_output_tokens=max_output_tokens,
                    reasoning_effort=reasoning_effort,
                    provider=active_provider,
                )
                amount = ledger.estimate(
                    payload,
                    model=pair_model,
                    provider=provider_name,
                    max_output_tokens=int(payload.get("max_output_tokens", payload.get("max_tokens", MAX_FINAL_OUTPUT_TOKENS))),
                ).amount
                per_system_amount[system] += amount
                per_provider_amount[provider_name] += amount
                max_calls += 1
            else:
                initial = active_provider.initial_request(
                    str(claim["claim"]),
                    pair_model,
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
                    for limit in (tool_limit, tool_limit * 2):
                        amount = ledger.estimate(
                            initial,
                            model=pair_model,
                            provider=provider_name,
                            max_output_tokens=limit,
                            previous_context=context if provider_name == META_PROVIDER else None,
                        ).amount
                        per_system_amount[system] += amount
                        per_provider_amount[provider_name] += amount
                final = _agent_final_payload(
                    str(claim["claim"]), pair_model, final_limit, reasoning_effort, provider_name
                )
                for limit in (final_limit, final_limit * 2):
                    amount = ledger.estimate(
                        final,
                        model=pair_model,
                        provider=provider_name,
                        max_output_tokens=limit,
                        previous_context=context if provider_name == META_PROVIDER else None,
                    ).amount
                    per_system_amount[system] += amount
                    per_provider_amount[provider_name] += amount
                max_calls += DEFAULT_MAX_TURNS * 2 + 2
    reservation = sum(per_system_amount.values())
    per_system = {}
    for system, amount in per_system_amount.items():
        method, provider_name = system_info[system]
        per_system[system] = {
            "claims": len(claims),
            "provider": provider_name,
            "max_model_calls": len(claims) if method == "single_shot" else len(claims) * (DEFAULT_MAX_TURNS * 2 + 2),
            "worst_case_reservation_usd": amount,
            "tools": method == "agent",
            **({"max_turns": DEFAULT_MAX_TURNS} if method == "agent" else {}),
        }
    return {
        "claims": len(claims),
        "splits": sorted({str(claim.get("split")) for claim in claims}),
        "systems": [canonical_system(system) for system in systems],
        "model": model
        or (
            default_model(next(iter({provider for _, provider in system_info.values()})))
            if len({provider for _, provider in system_info.values()}) == 1
            else "mixed"
        ),
        "models": {system: _model_for(model, provider) for system, (_, provider) in system_info.items()},
        "budget_usd": budget_usd,
        "out_dir": str(out_dir) if out_dir is not None else None,
        "max_model_calls": max_calls,
        "worst_case_reservation_usd": reservation,
        "provider_worst_case_reservation_usd": per_provider_amount,
        "provider_budgets_usd": {provider: budget_usd for provider in per_provider_amount},
        "budget_would_be_exceeded": any(amount > budget_usd for amount in per_provider_amount.values()),
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
    requested_system = canonical_system(system)
    by_id = {}
    for result in results:
        try:
            result_system = canonical_system(str(result.get("system") or ""))
        except ValueError:
            continue
        if result_system == requested_system and result.get("split") == split:
            by_id[str(result.get("id"))] = result
    predicted: dict[str, str] = {}
    latencies: list[float] = []
    costs: list[float] = []
    tokens = _zero_tokens()
    model_calls = 0
    tool_calls = 0
    errors: list[dict[str, Any]] = []
    for claim in expected:
        result = by_id.get(str(claim["id"]))
        if result is None:
            errors.append({"id": claim["id"], "category": "missing_result", "message": "no pair result"})
            continue
        verdict = result.get("verdict")
        if result.get("status") == "completed" and verdict in EVAL_VERDICTS:
            predicted[str(claim["id"])] = str(verdict)
            _add_tokens(tokens, result.get("tokens"))
            try:
                model_calls += max(0, int(result.get("model_calls", 0) or 0))
            except (TypeError, ValueError):
                pass
            try:
                tool_calls += max(0, int(result.get("tool_calls", 0) or 0))
            except (TypeError, ValueError):
                pass
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
        "system": requested_system,
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
        "tokens": tokens,
        "model_calls": model_calls,
        "tool_calls": tool_calls,
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


def _system_report_totals(
    results: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    for system in SYSTEMS:
        matching = []
        for result in results:
            try:
                result_system = canonical_system(str(result.get("system") or ""))
            except ValueError:
                continue
            if result_system == system:
                matching.append(result)
        latencies: list[float] = []
        costs = 0.0
        tokens = _zero_tokens()
        model_calls = 0
        tool_calls = 0
        completed = 0
        for result in matching:
            if result.get("status") == "completed":
                completed += 1
            try:
                costs += float(result.get("cost_usd", 0.0) or 0.0)
            except (TypeError, ValueError):
                pass
            _add_tokens(tokens, result.get("tokens"))
            try:
                result_model_calls = max(0, int(result.get("model_calls", 0) or 0))
            except (TypeError, ValueError):
                result_model_calls = 0
            model_calls += result_model_calls
            try:
                tool_calls += max(0, int(result.get("tool_calls", 0) or 0))
            except (TypeError, ValueError):
                pass
            try:
                latency = float(result.get("latency_ms"))
            except (TypeError, ValueError):
                latency = None
            if latency is not None and (result.get("status") == "completed" or result_model_calls > 0):
                latencies.append(latency)
        totals[system] = {
            "pairs": len(matching),
            "completed": completed,
            "cost_usd": {
                "total": costs,
                "mean": costs / len(matching) if matching else None,
            },
            "tokens": tokens,
            "model_calls": model_calls,
            "tool_calls": tool_calls,
            "latency_ms": {
                "mean": sum(latencies) / len(latencies) if latencies else None,
                "p50": _percentile(latencies, 50),
                "p95": _percentile(latencies, 95),
            },
        }
    return totals


def _tokens_cell(tokens: Any) -> str:
    if not isinstance(tokens, Mapping):
        return "—"
    return "/".join(str(int(tokens.get(key, 0) or 0)) for key in ("input", "cached", "output", "reasoning"))


def _provider_comparison(
    claims: Sequence[Mapping[str, Any]], results: Sequence[Mapping[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Aggregate provider-level quality and resource metrics across methods."""

    gold = {str(claim.get("id")): claim.get("gold_verdict") for claim in claims}
    comparison: dict[str, dict[str, Any]] = {}
    for provider in PROVIDERS:
        matching: list[Mapping[str, Any]] = []
        for result in results:
            try:
                _, result_provider = system_parts(str(result.get("system") or ""))
            except ValueError:
                continue
            if result_provider == provider:
                matching.append(result)
        completed = [
            result
            for result in matching
            if result.get("status") == "completed" and result.get("verdict") in EVAL_VERDICTS
        ]
        harmful = sum(
            gold.get(str(result.get("id"))) in {"contradicted", "insufficient_evidence"}
            for result in matching
        )
        false_supported = sum(
            result.get("status") == "completed"
            and result.get("verdict") == "supported"
            and gold.get(str(result.get("id"))) in {"contradicted", "insufficient_evidence"}
            for result in matching
        )
        correct = sum(
            result.get("status") == "completed"
            and result.get("verdict") == gold.get(str(result.get("id")))
            for result in matching
        )
        tokens = _zero_tokens()
        costs: list[float] = []
        latencies: list[float] = []
        for result in matching:
            _add_tokens(tokens, result.get("tokens"))
            if result.get("status") == "completed":
                try:
                    costs.append(float(result.get("cost_usd", 0.0) or 0.0))
                except (TypeError, ValueError):
                    pass
                try:
                    latencies.append(float(result.get("latency_ms", 0.0) or 0.0))
                except (TypeError, ValueError):
                    pass
        output_tokens = tokens["output"]
        comparison[provider] = {
            "provider": provider,
            "pairs": len(matching),
            "completed": len(completed),
            "accuracy": correct / len(matching) if matching else 0.0,
            "false_supported_rate": false_supported / harmful if harmful else 0.0,
            "false_supported": false_supported,
            "harmful_gold": harmful,
            "cost_usd": {
                "total": sum(costs),
                "mean": sum(costs) / len(costs) if costs else None,
            },
            "latency_ms": {
                "mean": sum(latencies) / len(latencies) if latencies else None,
                "p50": _percentile(latencies, 50),
                "p95": _percentile(latencies, 95),
            },
            "tokens": tokens,
            "reasoning_share": tokens["reasoning"] / output_tokens if output_tokens else 0.0,
        }
    return comparison


def _write_report(path: Path, summary: Mapping[str, Any], claims: Sequence[Mapping[str, Any]], results: Sequence[Mapping[str, Any]]) -> None:
    manifest = summary.get("manifest", {})
    if not isinstance(manifest, Mapping):
        manifest = {}
    lines = [
        "# Market claim evaluation report",
        "",
        f"Generated: {summary.get('generated_at', '—')}",
        f"Run window: {manifest.get('started_at', '—')} → {manifest.get('finished_at', '—')}",
        f"Wall clock: {_fmt_metric(manifest.get('wall_clock_s'), 3)} s",
        "",
        "Accuracy uses all expected claims in the denominator; a missing, failed, or budget-stopped pair is not a correct prediction. Per-class recall uses all claims of that gold class, while precision uses completed predictions of that class. False-supported rate is the harmful error rate among gold contradicted or insufficient-evidence claims. Latency and cost summaries use completed pairs only.",
        "",
        "No significance claims are made: each split is small (20 dev and 10 test claims).",
        "",
            "## Per-system totals",
            "",
            "Tokens are shown as input/cached/output/reasoning. Totals include every recorded pair; latency percentiles include pairs with a recorded model call.",
            "",
            "| System | Pairs | Completed | Total cost | Input tokens | Cached tokens | Output tokens | Reasoning tokens | Model calls | Tool calls | Mean latency ms | p50 ms | p95 ms |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    system_totals = summary.get("system_totals", {})
    if isinstance(system_totals, Mapping):
        for system in SYSTEMS:
            total = system_totals.get(system, {})
            if not isinstance(total, Mapping):
                continue
            tokens = total.get("tokens", {})
            latency = total.get("latency_ms", {})
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(system),
                        _md_cell(total.get("pairs", 0)),
                        _md_cell(total.get("completed", 0)),
                        _fmt_metric(_get(total.get("cost_usd", {}), "total"), 6),
                        _md_cell(_get(tokens, "input", 0)),
                        _md_cell(_get(tokens, "cached", 0)),
                        _md_cell(_get(tokens, "output", 0)),
                        _md_cell(_get(tokens, "reasoning", 0)),
                        _md_cell(total.get("model_calls", 0)),
                        _md_cell(total.get("tool_calls", 0)),
                        _fmt_metric(_get(latency, "mean"), 1),
                        _fmt_metric(_get(latency, "p50"), 1),
                        _fmt_metric(_get(latency, "p95"), 1),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Provider comparison",
            "",
            "Reasoning share is reasoning tokens divided by output tokens; provider totals include both methods.",
            "",
            "| Provider | Pairs | Completed | Accuracy | False-supported rate | Total cost | Mean latency ms | Input | Cached | Output | Reasoning | Reasoning share |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    provider_values = summary.get("provider_comparison", {})
    if isinstance(provider_values, Mapping):
        for provider in PROVIDERS:
            value = provider_values.get(provider, {})
            if not isinstance(value, Mapping):
                continue
            tokens = value.get("tokens", {})
            latency = value.get("latency_ms", {})
            cost = value.get("cost_usd", {})
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(provider),
                        _md_cell(value.get("pairs", 0)),
                        _md_cell(value.get("completed", 0)),
                        _fmt_metric(value.get("accuracy")),
                        _fmt_metric(value.get("false_supported_rate")),
                        _fmt_metric(_get(cost, "total"), 6),
                        _fmt_metric(_get(latency, "mean"), 1),
                        _md_cell(_get(tokens, "input", 0)),
                        _md_cell(_get(tokens, "cached", 0)),
                        _md_cell(_get(tokens, "output", 0)),
                        _md_cell(_get(tokens, "reasoning", 0)),
                        _fmt_metric(value.get("reasoning_share")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Prompt versions",
            "",
            "| Prompt | SHA-256 prefix |",
            "|---|---|",
        ]
    )
    prompt_registry_value = manifest.get("prompt_registry", {})
    if isinstance(prompt_registry_value, Mapping) and prompt_registry_value:
        for name, entry in prompt_registry_value.items():
            digest = entry.get("sha256") if isinstance(entry, Mapping) else None
            lines.append(f"| {_md_cell(name)} | {_md_cell(str(digest)[:12] if digest else None)} |")
    else:
        lines.append("| — | — |")
    lines.extend(
        [
            "",
        "## Metrics",
        "",
        "| System | Split | n | completed | errors | accuracy | false-supported rate | insufficient rate | mean latency ms | p50 ms | p95 ms | total cost | mean cost |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    )
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
            "Tokens are shown as input/cached/output/reasoning for each system.",
            "",
        ]
    )
    per_claim_header = ["ID", "Split", "Category", "Claim", "Gold"]
    for system in SYSTEMS:
        method, provider = system_parts(system)
        label = method.replace("_", " ").title()
        if provider != META_PROVIDER:
            label = f"{label}@{provider.title()}"
        per_claim_header.extend(
            [
                f"{label} verdict",
                f"{label} correct?",
                f"{label} cost",
                f"{label} latency ms",
                f"{label} tokens (i/c/o/r)",
            ]
        )
    lines.append("| " + " | ".join(per_claim_header) + " |")
    lines.append("|" + "---|" * len(per_claim_header))
    by_pair = {}
    for result in results:
        try:
            result_system = canonical_system(str(result.get("system") or ""))
        except ValueError:
            continue
        by_pair[(str(result.get("id")), result_system)] = result
    for claim in claims:
        values: list[str] = [
            str(claim["id"]),
            str(claim.get("split", "—")),
            _md_cell(claim.get("category")),
            _md_cell(claim.get("claim")),
            str(claim.get("gold_verdict", "—")),
        ]
        for system in SYSTEMS:
            result = by_pair.get((str(claim["id"]), system))
            if result is None:
                values.extend(["missing", "no", "—", "—", "—"])
            else:
                verdict = result.get("verdict") if result.get("status") == "completed" else f"{result.get('status', 'failed')}"
                correct = (
                    "yes"
                    if result.get("status") == "completed" and result.get("verdict") == claim.get("gold_verdict")
                    else "no"
                )
                values.extend(
                    [
                        str(verdict or "invalid"),
                        correct,
                        _fmt_metric(result.get("cost_usd", 0.0), 6),
                        _fmt_metric(result.get("latency_ms"), 1),
                        _tokens_cell(result.get("tokens")),
                    ]
                )
        lines.append("| " + " | ".join(_md_cell(value) for value in values) + " |")
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
            f"Budget stop: {manifest.get('budget_stop') or 'none recorded'}.",
            f"Ledger spend before/after: ${float(manifest.get('ledger_spend_before_usd', 0.0) or 0.0):.6f} / ${float(manifest.get('ledger_spend_after_usd', 0.0) or 0.0):.6f}.",
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
        for system in SYSTEMS
        if system.startswith("agent@")
        for split_metrics in metrics.get(system, {}).values()
        for error in split_metrics.get("errors", [])
    ]
    summary: dict[str, Any] = {
        "generated_at": _now(),
        "out_dir": str(out),
        "manifest": manifest,
        "metrics": {system: dict(split_metrics) for system, split_metrics in metrics.items()},
        "system_totals": _system_report_totals(results),
        "provider_comparison": _provider_comparison(claims, results),
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
