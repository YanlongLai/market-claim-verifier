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

    verify = subparsers.add_parser("verify", help="verify a financial claim with Muse")
    verify.add_argument("claim")
    verify.add_argument("--provider", choices=PROVIDERS)
    verify.add_argument("--model")
    verify.add_argument("--budget", type=float)
    verify.add_argument("--max-output-tokens", type=_positive_int)
    verify.add_argument("--reasoning-effort")
    verify.add_argument("--dry-run", action="store_true")

    evaluation = subparsers.add_parser("eval", help="run or report the labeled evaluation")
    evaluation_subparsers = evaluation.add_subparsers(dest="eval_action", required=True)

    run = evaluation_subparsers.add_parser("run", help="run evaluation pairs sequentially")
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

    report = evaluation_subparsers.add_parser("report", help="write summary.json and REPORT.md")
    report.add_argument("--out", type=Path, required=True)
    report.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS_PATH)

    prompts = subparsers.add_parser("prompts", help="export versioned prompt source files")
    prompts_subparsers = prompts.add_subparsers(dest="prompts_action", required=True)
    prompts_subparsers.add_parser("export", help="write prompts/*.md from the code prompts")
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
            args.command == "verify" and not getattr(args, "dry_run", False)
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
        )
        result = edgar.lookup_fact(args.ticker, args.metric, args.period)
        _print_json(result)
        return 0 if "error" not in result else 1

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
            claims = load_claims(args.claims)
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
                key_name = "BASETEN_API_KEY" if provider == "baseten" else "MODEL_API_KEY"
                key_path = value.baseten_api_key_file if provider == "baseten" else value.model_api_key_file
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
            )
        except (EvaluationError, BudgetExceeded, UnknownModel, ValueError) as exc:
            print(f"Evaluation run failed: {exc}", file=sys.stderr)
            return 1
        _print_json(manifest)
        return 0

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
        _print_json({"request": request, "reservation": reservation.as_dict()})
        return 0

    if not settings.model_api_key:
        print(
            f"Missing {provider} model API key. Set "
            f"{'BASETEN_API_KEY' if provider == 'baseten' else 'MODEL_API_KEY'} or put the raw key in "
            f"{settings.baseten_api_key_file if provider == 'baseten' else settings.model_api_key_file}.",
            file=sys.stderr,
        )
        return 2

    try:
        client = create_client(provider, settings.model_api_key)
        edgar = EdgarClient(
            cache_dir=settings.cache_dir,
            user_agent=settings.sec_user_agent,
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
