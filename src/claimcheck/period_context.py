"""Conservative, source-backed period inheritance before financial verification."""
from __future__ import annotations

import re
from typing import Any

_QUARTER = r"(?:Q[1-4]|(?:first|second|third|fourth|[1-4](?:st|nd|rd|th))\s+quarter)"
_YEAR = r"(?:19|20)\d{2}"
_PERIOD = re.compile(
    rf"\b(?:(?:fiscal\s*|calendar\s*|FY\s*)?(?P<y>{_YEAR})\s*[-,/]?\s*(?P<q>{_QUARTER})"
    rf"|(?:(?:fiscal|calendar)\s*)?(?P<q2>{_QUARTER})\s*(?:of\s+)?(?:FY\s*|fiscal\s*)?(?P<y2>{_YEAR}))\b", re.I)
_ANNUAL = re.compile(rf"\b(?:FY\s*|fiscal\s+(?:year\s+)?)(?P<y>{_YEAR})\b", re.I)
_NUMBER = re.compile(r"\d")
_QUANTIFIED = re.compile(r'\b(?:growth|grew|rose|fell|doubled|tripled|percent|million|billion|trillion|hundred|dollars)\b', re.I)
_METRIC = re.compile(r"\b(?:growth|revenue|sales|income|profit|earnings|EPS|margin|cash|assets|debt|dividend|EBITDA|expenses|costs|guidance|outlook)\b", re.I)


def period_mentions(text: str) -> list[dict[str, Any]]:
    mentions = []
    for match in _PERIOD.finditer(text):
        quarter = (match['q'] or match['q2']).lower()
        digit = re.search(r"[1-4]", quarter)
        q = digit[0] if digit else str(('first', 'second', 'third', 'fourth').index(quarter.split()[0]) + 1)
        year = match['y'] or match['y2']
        basis = 'calendar' if 'calendar' in match[0].lower() else 'fiscal' if re.search(r'fiscal|FY', match[0], re.I) else None
        mentions.append({'text': match[0], 'span': list(match.span()), 'period': f'{year}Q{q}', 'basis': basis})
    for match in _ANNUAL.finditer(text):
        if not any(match.start() < m['span'][1] and match.end() > m['span'][0] for m in mentions):
            mentions.append({'text': match[0], 'span': list(match.span()), 'period': match['y'], 'basis': 'fiscal'})
    return sorted(mentions, key=lambda m: m['span'][0])


def missing_period_reason(claim: str) -> str | None:
    """A relative phrase alone cannot authorize choosing the latest filed period."""
    years = [m for m in re.finditer(rf'\b{_YEAR}\b', claim)
             if not re.search(r'\$\s*$', claim[:m.start()]) and not re.match(r'\s*(?:dollars|%)', claim[m.end():], re.I)]
    if (_NUMBER.search(claim) or _QUANTIFIED.search(claim)) and _METRIC.search(claim) and not (period_mentions(claim) or years):
        return 'missing_period: numeric financial claim has no explicit year or dated period; refusing to guess the latest period'
    return None


def inherit_period(post: str, span: tuple[int, int], claim: str) -> tuple[str, dict[str, Any] | None]:
    """Use a unique nearby stated period; leave mixed-period context unresolved.

    This never reads filings or the clock. Context and offsets are input claims,
    not evidence. The original quote remains unchanged for the number guard.
    """
    if missing_period_reason(claim) is None:
        return claim, None
    start, end = span
    own = period_mentions(post[start:end])
    # Include the surrounding turn/slide and preceding period introduction.
    left = max(0, start - 2400)
    candidates = own or period_mentions(post[left:start])
    offset = start if own else left
    if not candidates:
        # An adjacent period phrase can follow a row or short spoken clause.
        tail = post[end:end + 400].split('\n\n')[0]
        candidates = period_mentions(tail)
        offset = end
    if len({(m['period'], m['basis']) for m in candidates}) != 1:
        return claim, None
    chosen = dict(candidates[-1])
    chosen['span'] = [p + offset for p in chosen['span']]
    chosen['scope'] = 'quoted text' if own else 'nearby document/turn heading'
    period = chosen['period']
    basis = (chosen['basis'] + ' ') if chosen['basis'] else ''
    label = f'{basis}Q{period[-1]} {period[:4]}' if 'Q' in period else f'{basis}year {period}'
    return f'{claim.rstrip(". ")} for {label}.', chosen
