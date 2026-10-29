"""Render a verified L4 quote with its program-owned character highlights."""
from __future__ import annotations

import html
from typing import Any, Mapping


def render_release_quote(evidence: Mapping[str, Any]) -> str:
    quote = str(evidence.get("quote") or "")
    if not quote:
        return ""
    start = int(evidence.get("quote_start", evidence.get("start", 0)))
    end = start + len(quote)
    parts, cursor = [], 0
    for a, b in sorted(evidence.get("highlight_offsets") or []):
        a, b = a - start, b - start
        if not 0 <= cursor <= a < b <= len(quote):
            continue
        parts.extend([html.escape(quote[cursor:a]), "<mark>", html.escape(quote[a:b]), "</mark>"])
        cursor = b
    parts.append(html.escape(quote[cursor:]))
    return f'<blockquote data-start="{start}" data-end="{end}">' + "".join(parts) + "</blockquote>"
