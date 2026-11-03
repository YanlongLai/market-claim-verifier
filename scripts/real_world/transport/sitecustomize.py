"""Evaluation-only CLI transport: explicit SDK retries=0, request timeout=90s.

Loaded only by the runner's post subprocess PYTHONPATH. Production prompts,
parsing, tools, application retries, extraction and program checks are untouched.
Every application attempt remains separately reserved by claimcheck.budget.
"""
from openai import OpenAI

_original_init = OpenAI.__init__


def _bounded_init(self, *args, **kwargs):
    kwargs["max_retries"] = 0
    kwargs.setdefault("timeout", 90.0)
    _original_init(self, *args, **kwargs)


OpenAI.__init__ = _bounded_init
