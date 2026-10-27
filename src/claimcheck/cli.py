"""Command-line interface for EDGAR lookups and claim verification."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from typing import Sequence

from .agent import MAX_TOOL_OUTPUT_TOKENS, initial_request, verify_claim
from .budget import BudgetExceeded, Ledger, UnknownModel
from .config import SettingsError, load_settings
from .edgar import EdgarClient
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
    verify.add_argument("--model")
    verify.add_argument("--budget", type=float)
    verify.add_argument("--dry-run", action="store_true")
    return parser


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        # EDGAR and dry-run commands do not need to inspect a key file.
        settings = load_settings(read_key=args.command == "verify" and not args.dry_run)
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

    model = args.model or settings.model
    budget = settings.budget_usd if args.budget is None else args.budget
    settings = replace(settings, model=model, budget_usd=budget)
    ledger = Ledger(settings.runs_dir / "ledger.jsonl", budget_usd=settings.budget_usd)
    request = initial_request(args.claim, model)
    if args.dry_run:
        try:
            reservation = ledger.preview(
                request,
                model=model,
                max_output_tokens=MAX_TOOL_OUTPUT_TOKENS,
            )
        except (BudgetExceeded, UnknownModel) as exc:
            print(f"Dry-run refused: {exc}", file=sys.stderr)
            return 2
        _print_json({"request": request, "reservation": reservation.as_dict()})
        return 0

    if not settings.model_api_key:
        print(
            "Missing model API key. Set MODEL_API_KEY or put "
            f"MODEL_API_KEY=... in {settings.model_api_key_file}.",
            file=sys.stderr,
        )
        return 2

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url="https://api.meta.ai/v1",
            api_key=settings.model_api_key,
        )
        edgar = EdgarClient(
            cache_dir=settings.cache_dir,
            user_agent=settings.sec_user_agent,
        )
        recorder = TraceRecorder(
            args.claim,
            model,
            secrets=[settings.model_api_key],
        )
        result = verify_claim(
            args.claim,
            client,
            edgar,
            ledger,
            model,
            trace=recorder,
        )
        trace_path = write_trace(settings.runs_dir, recorder)
        result = {**result, "trace_path": str(trace_path)}
        _print_json(result)
        return 0
    except (BudgetExceeded, UnknownModel) as exc:
        print(f"Verification refused: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        return 1
