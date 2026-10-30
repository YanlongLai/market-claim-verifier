"""Command-line interface for EDGAR lookups and claim verification."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .agent import initial_request, verify_claim
from .budget import BudgetExceeded, Ledger, UnknownModel
from .config import SettingsError, load_settings
from .data_quality import (
    DEFAULT_DOC_PATH,
    DEFAULT_REPORT_PATH,
    DEFAULT_SNAPSHOT_DATE,
    write_data_quality_artifacts,
)
from .edgar import EdgarClient
from .evaluate import (
    DEFAULT_BUDGET_USD as DEFAULT_EVAL_BUDGET_USD,
    DEFAULT_CLAIMS_PATH,
    EvaluationError,
    SYSTEMS,
    dry_run_plan,
    load_claims,
    report_evaluation,
    run_evaluation,
)
from .prompts import export_prompt_files
from .providers import (
    PROVIDERS,
    canonical_system,
    create_client,
    system_parts,
)
from .trace import TraceRecorder, write_trace


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m claimcheck")
    subparsers = parser.add_subparsers(dest="command", required=True)

    edgar = subparsers.add_parser("edgar", help="look up a cached SEC EDGAR fact")
    edgar.add_argument("ticker")
    edgar.add_argument("metric")
    edgar.add_argument("period")

    quality = subparsers.add_parser(
        "data-quality", help="check the cached SEC companyfacts snapshot"
    )
    quality.add_argument("--cache-dir", type=Path)
    quality.add_argument("--snapshot-date", default=DEFAULT_SNAPSHOT_DATE)
    quality.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    quality.add_argument("--doc", type=Path, default=DEFAULT_DOC_PATH)

    verify = subparsers.add_parser("verify", help="verify a financial claim with Muse")
    verify.add_argument("claim")
    verify.add_argument("--provider", choices=PROVIDERS)
    verify.add_argument("--model")
    verify.add_argument("--budget", type=float)
    verify.add_argument("--max-output-tokens", type=_positive_int)
    verify.add_argument("--reasoning-effort")
    verify.add_argument("--dry-run", action="store_true")

    post = subparsers.add_parser(
        "post", help="extract and verify every financial claim in a pasted post or article"
    )
    post.add_argument("file", help="text file with the post, or - for stdin")
    post.add_argument("--provider", choices=PROVIDERS)
    post.add_argument("--model")
    post.add_argument("--budget", type=float)
    post.add_argument("--max-claims", type=_positive_int, default=8)
    post.add_argument("--max-output-tokens", type=_positive_int)
    post.add_argument("--reasoning-effort")
    post.add_argument("--out", type=Path, help="output directory (default runs/posts/<UTC time>)")

    ingest = subparsers.add_parser("ingest", help="decode text, PDF, screenshot, audio or video and check its claims")
    ingest.add_argument("file", type=Path)
    ingest.add_argument("--provider", choices=PROVIDERS)
    ingest.add_argument("--model")
    ingest.add_argument("--budget", type=float)
    ingest.add_argument("--max-claims", type=_positive_int, default=8)
    ingest.add_argument("--max-output-tokens", type=_positive_int)
    ingest.add_argument("--reasoning-effort")
    ingest.add_argument("--out", type=Path, help="output directory (default runs/ingest/<UTC time>)")

    queue = subparsers.add_parser("queue", help="run/resume a bounded serial ingestion queue against frozen SEC evidence")
    queue.add_argument("files", nargs="+", type=Path)
    queue.add_argument("--out", type=Path, required=True)
    queue.add_argument("--evidence-cache", type=Path, required=True)
    queue.add_argument("--budget", type=float, required=True)
    queue.add_argument("--per-job-budget", type=float, required=True)
    queue.add_argument("--max-jobs", type=_positive_int, default=10)
    queue.add_argument("--provider", choices=PROVIDERS)
    queue.add_argument("--model")
    queue.add_argument("--max-claims", type=_positive_int, default=8)
    queue.add_argument("--max-output-tokens", type=_positive_int)
    queue.add_argument("--reasoning-effort")

    stock = subparsers.add_parser("stock-summary", help="summarize retained ingestion reports for one ticker without model calls")
    stock.add_argument("ticker")
    stock.add_argument("reports", nargs="+", type=Path)
    stock.add_argument("--out", type=Path, required=True)
    review = subparsers.add_parser("review-stock", help="check multiple local files and summarize one stock")
    review.add_argument("ticker")
    review.add_argument("files", nargs="+", type=Path)
    review.add_argument("--out", type=Path, required=True)
    review.add_argument("--evidence-cache", type=Path, required=True)
    review.add_argument("--budget", type=float, required=True)
    review.add_argument("--per-job-budget", type=float, required=True)
    review.add_argument("--max-jobs", type=_positive_int, default=10)
    review.add_argument("--provider", choices=PROVIDERS)
    review.add_argument("--model")
    review.add_argument("--max-claims", type=_positive_int, default=8)
    review.add_argument("--max-output-tokens", type=_positive_int)
    review.add_argument("--reasoning-effort")

    evaluation = subparsers.add_parser("eval", help="run or report the labeled evaluation")
    evaluation_subparsers = evaluation.add_subparsers(dest="eval_action", required=True)

    run = evaluation_subparsers.add_parser("run", help="run evaluation pairs with bounded concurrency")
    run.add_argument("--split", choices=("dev", "test", "all"), default="all")
    run.add_argument("--systems", default=",".join(SYSTEMS))
    run.add_argument("--provider", choices=PROVIDERS)
    run.add_argument("--model")
    run.add_argument("--budget", type=float, default=None)
    run.add_argument("--out", type=Path)
    run.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS_PATH)
    run.add_argument("--max-output-tokens", type=_positive_int)
    run.add_argument("--reasoning-effort")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--concurrency", type=_positive_int, default=1)

    report = evaluation_subparsers.add_parser("report", help="write summary.json and REPORT.md")
    report.add_argument("--out", type=Path, required=True)
    report.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS_PATH)

    prompts = subparsers.add_parser("prompts", help="export versioned prompt source files")
    prompts_subparsers = prompts.add_subparsers(dest="prompts_action", required=True)
    prompts_subparsers.add_parser("export", help="write prompts/*.md from the code prompts")
    from .policy import parse_as_of
    for command_parser in (edgar, verify, post, ingest, queue, review):
        command_parser.add_argument('--as-of', type=parse_as_of, metavar='YYYY-MM-DD',
                                    help='include only evidence filed on or before this date (inclusive)')
    return parser


def _positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def _parse_systems(raw: str, *, provider: str | None = None) -> tuple[str, ...]:
    raw_systems = tuple(part.strip() for part in raw.split(",") if part.strip())
    systems = tuple(
        canonical_system(system, provider=provider)
        if "@" not in system
        else canonical_system(system)
        for system in raw_systems
    )
    if not systems or any(system not in SYSTEMS for system in systems):
        raise EvaluationError(
            f"systems must be a comma-separated subset of {','.join(SYSTEMS)}"
        )
    if len(set(systems)) != len(systems):
        raise EvaluationError("systems must not contain duplicates")
    return systems


def _default_eval_out() -> Path:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return Path("docs/evidence") / f"eval-{day}"


def main(argv: Sequence[str] | None = None) -> int:
    cli_args = list(argv) if argv is not None else sys.argv[1:]
    args = _parser().parse_args(argv)
    try:
        # EDGAR, evaluation reports, and dry runs do not need to inspect a key file.
        reads_key = (
            args.command in {"verify", "post", "ingest", "queue", "review-stock"} and not getattr(args, "dry_run", False)
        ) or (
            args.command == "eval"
            and args.eval_action == "run"
            and not args.dry_run
        )
        settings = load_settings(
            read_key=reads_key,
            provider=getattr(args, "provider", None),
        )
    except SettingsError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    if args.command == "edgar":
        edgar = EdgarClient(
            cache_dir=settings.cache_dir,
            user_agent=settings.sec_user_agent,
            as_of=getattr(args, "as_of", None),
        )
        result = edgar.lookup_fact(args.ticker, args.metric, args.period)
        result["verification_policy"] = edgar.policy.to_dict()
        _print_json(result)
        return 0 if "error" not in result else 1

    if args.command == "data-quality":
        try:
            report = write_data_quality_artifacts(
                args.cache_dir or settings.cache_dir,
                snapshot_date=args.snapshot_date,
                report_path=args.report,
                doc_path=args.doc,
            )
        except (OSError, ValueError, KeyError) as exc:
            print(f"Data-quality report failed: {exc}", file=sys.stderr)
            return 1
        _print_json(
            {
                "snapshot_date": report.get("snapshot_date"),
                "issuer_count": report.get("issuer_count", 0),
                "report": str(args.report),
                "doc": str(args.doc),
            }
        )
        return 0

    if args.command == "prompts":
        if args.prompts_action == "export":
            paths = export_prompt_files()
            _print_json({"directory": "prompts", "files": [str(path) for path in paths]})
            return 0

    if args.command == "eval":
        if args.eval_action == "report":
            try:
                summary = report_evaluation(args.out, claims_path=args.claims)
            except (EvaluationError, OSError, ValueError) as exc:
                print(f"Evaluation report failed: {exc}", file=sys.stderr)
                return 1
            _print_json(
                {
                    "out": str(args.out),
                    "summary": str(args.out / "summary.json"),
                    "report": str(args.out / "REPORT.md"),
                    "result_count": summary.get("result_count", 0),
                }
            )
            return 0

        try:
            systems = _parse_systems(args.systems, provider=args.provider)
            # v1 keeps its strict 30-claim contract; v2 and future frozen
            # manifests are validated structurally by the runner instead.
            claims = load_claims(args.claims, strict=False)
            if args.split != "all":
                claims = [claim for claim in claims if claim.get("split") == args.split]
            model = args.model or (settings.model if os.environ.get("CLAIMCHECK_MODEL") else None)
            budget = DEFAULT_EVAL_BUDGET_USD if args.budget is None else args.budget
            out_dir = args.out or _default_eval_out()
            max_output_tokens = (
                args.max_output_tokens
                if args.max_output_tokens is not None
                else settings.max_output_tokens
            )
            reasoning_effort = (
                args.reasoning_effort
                if args.reasoning_effort is not None
                else settings.reasoning_effort
            )
            if args.dry_run:
                _print_json(
                    {
                        "plan": dry_run_plan(
                            claims,
                            systems=systems,
                            model=model,
                            budget_usd=budget,
                            max_output_tokens=max_output_tokens,
                            reasoning_effort=reasoning_effort,
                            out_dir=out_dir,
                            concurrency=args.concurrency,
                        )
                    }
                )
                return 0
            provider_names = {system_parts(system)[1] for system in systems}
            provider_settings = {
                provider: load_settings(provider=provider, read_key=True)
                for provider in provider_names
            }
            missing = [provider for provider, value in provider_settings.items() if not value.model_api_key]
            if missing:
                provider = missing[0]
                value = provider_settings[provider]
                if provider == "baseten":
                    key_name = "BASETEN_API_KEY"
                    key_path = value.baseten_api_key_file
                elif provider == "fireworks":
                    key_name = "FIREWORKS_API_KEY"
                    key_path = value.fireworks_api_key_file
                else:
                    key_name = "MODEL_API_KEY"
                    key_path = value.model_api_key_file
                print(
                    f"Missing {provider} model API key. Set {key_name} or put the raw key in {key_path}.",
                    file=sys.stderr,
                )
                return 2
            clients = {
                provider: create_client(provider, value.model_api_key or "")
                for provider, value in provider_settings.items()
            }
            secrets = {
                provider: [value.model_api_key]
                for provider, value in provider_settings.items()
                if value.model_api_key
            }
            manifest = run_evaluation(
                claims,
                systems=systems,
                model=model,
                budget_usd=budget,
                out_dir=out_dir,
                client=clients,
                cache_dir=settings.cache_dir,
                max_output_tokens=max_output_tokens,
                reasoning_effort=reasoning_effort,
                secrets=secrets,
                split=args.split,
                cli_args=cli_args,
                claims_path=args.claims,
                concurrency=args.concurrency,
            )
        except (EvaluationError, BudgetExceeded, UnknownModel, ValueError) as exc:
            print(f"Evaluation run failed: {exc}", file=sys.stderr)
            return 1
        _print_json(manifest)
        return 0

    if args.command == "stock-summary":
        from .stock_review import build_stock_review
        try:
            report = build_stock_review(args.ticker, args.reports, args.out)
        except (ValueError, OSError) as exc:
            print(f"Stock summary refused: {exc}", file=sys.stderr)
            return 2
        _print_json({"out": str(args.out), "summary": report["summary"], "incremental_api_cost_usd": 0})
        return 0

    if args.command in ("queue", "review-stock"):
        if args.command == "review-stock":
            import re
            if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,9}", args.ticker.strip().upper()):
                print("Invalid US ticker; no jobs started.", file=sys.stderr)
                return 2
        from .job_queue import run_queue, cli_worker
        from .policy import VerificationPolicy
        config = {"provider": settings.provider, "model": args.model or settings.model,
                  "as_of": args.as_of, "policy": VerificationPolicy(as_of=args.as_of).to_dict(),
                  "budget_usd": args.budget, "per_job_budget_usd": args.per_job_budget,
                  "max_claims": args.max_claims,
                  "max_output_tokens": args.max_output_tokens or settings.max_output_tokens,
                  "reasoning_effort": args.reasoning_effort or settings.reasoning_effort}
        try:
            queue_out = args.out / "queue" if args.command == "review-stock" else args.out
            state = run_queue(args.files, args.evidence_cache, queue_out, config,
                              cli_worker(settings, config), max_jobs=args.max_jobs)
            if args.command == "review-stock":
                from .stock_review import build_stock_review
                reports = [queue_out / job["out"] / "ingest.json" for job in state["jobs"]
                           if (queue_out / job["out"] / "ingest.json").exists()]
                pending = [{"input": {"file": state["identity"]["inputs"][job["id"]]["name"]},
                            "status": job["status"], "reason": job.get("reason", "No ingestion report available")}
                           for job in state["jobs"] if not (queue_out / job["out"] / "ingest.json").exists()]
                # Each invocation preserves the previous partial summary.
                n = len(list(args.out.glob("summary-*"))) + 1
                build_stock_review(args.ticker, reports, args.out / f"summary-{n:03d}", pending_documents=pending)
        except (ValueError, OSError) as exc:
            print(f"Queue refused: {exc}", file=sys.stderr)
            return 2
        _print_json({"out": str(args.out), "status": state["status"],
                     "admitted_budget_usd": state["admitted_budget_usd"],
                     "jobs": [{"id": j["id"], "status": j["status"]} for j in state["jobs"]]})
        return 0 if state['status'] == 'completed' else 1

    if args.command == "post":
        return _run_post(args, settings)

    if args.command == "ingest":
        return _run_ingest(args, settings)

    model = args.model or settings.model
    provider = settings.provider
    budget = settings.budget_usd if args.budget is None else args.budget
    max_output_tokens = (
        args.max_output_tokens
        if args.max_output_tokens is not None
        else settings.max_output_tokens
    )
    reasoning_effort = (
        args.reasoning_effort
        if args.reasoning_effort is not None
        else settings.reasoning_effort
    )
    settings = replace(
        settings,
        provider=provider,
        model=model,
        budget_usd=budget,
        max_output_tokens=max_output_tokens,
        reasoning_effort=reasoning_effort,
    )
    ledger = Ledger(
        settings.runs_dir / "ledger.jsonl",
        budget_usd=settings.budget_usd,
        provider=provider,
    )
    request = initial_request(
        args.claim,
        model,
        max_output_tokens=max_output_tokens,
        reasoning_effort=reasoning_effort,
        provider=provider,
    )
    if args.dry_run:
        try:
            reservation = ledger.preview(
                request,
                model=model,
                max_output_tokens=int(request.get("max_output_tokens", request.get("max_tokens", 0))),
                provider=provider,
            )
        except (BudgetExceeded, UnknownModel) as exc:
            print(f"Dry-run refused: {exc}", file=sys.stderr)
            return 2
        from .policy import VerificationPolicy
        _print_json({"request": request, "reservation": reservation.as_dict(),
                     "verification_policy": VerificationPolicy(as_of=getattr(args, "as_of", None)).to_dict()})
        return 0

    if not settings.model_api_key:
        print(
            f"Missing {provider} model API key. Set "
            f"{('BASETEN_API_KEY' if provider == 'baseten' else 'FIREWORKS_API_KEY' if provider == 'fireworks' else 'MODEL_API_KEY')} or put the raw key in "
            f"{(settings.baseten_api_key_file if provider == 'baseten' else settings.fireworks_api_key_file if provider == 'fireworks' else settings.model_api_key_file)}.",
            file=sys.stderr,
        )
        return 2

    try:
        client = create_client(provider, settings.model_api_key)
        edgar = EdgarClient(
            cache_dir=settings.cache_dir,
            user_agent=settings.sec_user_agent,
            as_of=getattr(args, "as_of", None),
        )
        recorder = TraceRecorder(
            args.claim,
            model,
            provider=provider,
            secrets=[settings.model_api_key],
        )
        result = verify_claim(
            args.claim,
            client,
            edgar,
            ledger,
            model,
            trace=recorder,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
            provider=provider,
        )
        trace_path = write_trace(settings.runs_dir, recorder)
        result = {**result, "trace_path": str(trace_path), **recorder.summary()}
        _print_json(result)
        return 0
    except (BudgetExceeded, UnknownModel) as exc:
        print(f"Verification refused: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        return 1


def _run_post(args: argparse.Namespace, settings: object) -> int:
    from .post import PostError, check_post

    text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    provider = settings.provider
    model = args.model or settings.model
    budget = settings.budget_usd if args.budget is None else args.budget
    if not settings.model_api_key:
        print(f"Missing {provider} model API key.", file=sys.stderr)
        return 2
    out = args.out or settings.runs_dir / "posts" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ledger = Ledger(settings.runs_dir / "ledger.jsonl", budget_usd=budget, provider=provider)
    try:
        report = check_post(
            text,
            client=create_client(provider, settings.model_api_key),
            edgar=EdgarClient(cache_dir=settings.cache_dir, user_agent=settings.sec_user_agent, as_of=getattr(args, "as_of", None)),
            ledger=ledger,
            model=model,
            provider=provider,
            out_dir=Path(out),
            max_claims=args.max_claims,
            secrets=[settings.model_api_key],
            max_output_tokens=args.max_output_tokens or settings.max_output_tokens,
            reasoning_effort=args.reasoning_effort or settings.reasoning_effort,
        )
    except (BudgetExceeded, UnknownModel) as exc:
        print(f"Post check refused: {exc}", file=sys.stderr)
        return 2
    except PostError as exc:
        print(f"Post check failed: {exc}", file=sys.stderr)
        return 1
    _print_json({
        "out": str(out),
        "report": str(Path(out) / "report.html"),
        "counts": report["counts"],
        "verdicts": report["verdicts"],
        "cost_usd": report["cost_usd"],
        "claims": [
            {k: item.get(k) for k in ("index", "quote", "claim", "kind", "status", "verdict", "screen_reason")}
            for item in report["claims"]
        ],
    })
    return 0


def _run_ingest(args: argparse.Namespace, settings: object) -> int:
    import math
    import httpx
    from .ingest import ingest_file
    from .ingest_media import IngestError

    budget = settings.budget_usd if args.budget is None else args.budget
    if not math.isfinite(budget) or budget < 0:
        print("Ingest budget must be finite and non-negative", file=sys.stderr)
        return 2
    out = args.out or settings.runs_dir / "ingest" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    meta = settings if settings.provider == "meta" else load_settings(provider="meta")
    # One total cap, partitioned for mixed-provider runs. Both model families are Meta.
    budgets = {"meta": budget} if settings.provider == "meta" else {"meta": budget / 2, settings.provider: budget / 2}
    ledger = Ledger(settings.runs_dir / "ingest-ledger.jsonl", budget_usd=budget,
                    provider=settings.provider, provider_budgets=budgets)
    client = create_client(settings.provider, settings.model_api_key).with_options(max_retries=0) if settings.model_api_key else None
    vision = client if settings.provider == "meta" else create_client("meta", meta.model_api_key).with_options(max_retries=0) if meta.model_api_key else None
    secrets = [key for key in (settings.model_api_key, meta.model_api_key) if key]
    try:
        with httpx.Client(timeout=120) as http:
            report = ingest_file(args.file, client=client, vision_client=vision, asr_http=http,
                meta_api_key=meta.model_api_key, edgar=EdgarClient(cache_dir=settings.cache_dir, user_agent=settings.sec_user_agent, as_of=getattr(args, "as_of", None)),
                ledger=ledger, model=args.model or settings.model, provider=settings.provider, out_dir=out,
                max_claims=args.max_claims, secrets=secrets,
                max_output_tokens=args.max_output_tokens or settings.max_output_tokens,
                reasoning_effort=args.reasoning_effort or settings.reasoning_effort)
    except (IngestError, BudgetExceeded, UnknownModel) as exc:
        print(f"Ingest refused: {exc}", file=sys.stderr)
        return 2
    _print_json({"out": str(out), "report": str(out / "ingest.html"), "status": report["status"],
                 "stages": report["stages"], "cost_usd": report["cost_usd"], "wall_clock_s": report["wall_clock_s"]})
    return 0 if report["status"] == "completed" else 1
