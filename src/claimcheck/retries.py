"""Small explicit retry policy; SDK retries stay disabled by runtime callers."""
from __future__ import annotations

import re
import time
from typing import Any

MAX_ATTEMPTS = 3
TRANSIENT_STATUS = {500, 502, 503, 504}


def retry_info(status: int | None, attempt: int) -> dict[str, Any]:
    transient = status in TRANSIENT_STATUS
    retry = transient and attempt < MAX_ATTEMPTS
    return {'attempt': attempt, 'max_attempts': MAX_ATTEMPTS, 'http_status': status,
            'transient': transient, 'next_delay_s': min(2 ** (attempt - 1), 4) if retry else None,
            'exhausted': transient and not retry}


def wait_for_retry(info: dict[str, Any]) -> bool:
    if info['next_delay_s'] is None:
        return False
    time.sleep(info['next_delay_s'])
    return True


def exception_status(exc: BaseException) -> int | None:
    status = getattr(exc, 'status_code', None)
    if not isinstance(status, int):
        status = getattr(getattr(exc, 'response', None), 'status_code', None)
    return status if isinstance(status, int) else None


OVERLOAD_STATUS = {503, 529}


def provider_overloaded(status: int | None, body: str = '') -> bool:
    """503/529, or a 429/500/502 whose body says overloaded or at capacity.

    Used by the live server, the worker and the CLI so all three name the same failure.
    Only the classification is kept; provider response bodies are never logged.
    """
    if status in OVERLOAD_STATUS:
        return True
    text = (body or '')[:16384].lower()
    return status in (429, 500, 502) and bool(re.search(r'overload|at capacity|over capacity', text))


def overloaded_exception(exc: BaseException) -> bool:
    return provider_overloaded(exception_status(exc), str(exc))
