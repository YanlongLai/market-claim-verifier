"""One process-wide SEC fair-access gate shared by XBRL and releases."""

from __future__ import annotations

import threading
import time

import httpx


_LOCK = threading.Lock()
_last_request = 0.0
USER_AGENT = "DappGo market-claim-verifier admin@dappgo.com"


def sec_get(url: str, *, user_agent: str = USER_AGENT, timeout: float = 20.0) -> bytes:
    """Start at most nine requests per second, including concurrent clients."""
    global _last_request
    with _LOCK:
        delay = 1 / 9 - (time.monotonic() - _last_request)
        if delay > 0:
            time.sleep(delay)
        _last_request = time.monotonic()
    response = httpx.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
    response.raise_for_status()
    return response.content
