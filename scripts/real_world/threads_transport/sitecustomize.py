"""Evaluation-only transport and shared caps for actual phase-2 CLI calls.

Required environment is installed by run_threads.py. Prompts, extraction,
retrieval, retry policy and program verdicts remain production code.
"""
import os

from openai import OpenAI
from claimcheck.budget import Ledger

_client_init = OpenAI.__init__
_ledger_init = Ledger.__init__


def _bounded_client(self, *args, **kwargs):
    kwargs["max_retries"] = 0
    kwargs.setdefault("timeout", 90.0)
    _client_init(self, *args, **kwargs)


def _shared_ledger(self, *args, **kwargs):
    if not os.environ.get("MCV_PHASE2_LEDGER"):
        raise RuntimeError("phase-2 shared ledger path required")
    kwargs.update(budget_usd=8, provider_budgets={p: 8 for p in ("baseten", "fireworks", "meta")})
    kwargs.pop("path", None)
    _ledger_init(self, os.environ["MCV_PHASE2_LEDGER"], **kwargs)


OpenAI.__init__ = _bounded_client
Ledger.__init__ = _shared_ledger
