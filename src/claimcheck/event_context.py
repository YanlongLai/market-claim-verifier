"""Explicit, reviewable event periods; never treated as spoken text or evidence."""
from __future__ import annotations
import re
from urllib.parse import urlsplit
from .period_context import period_mentions, missing_period_reason


def validate_event_context(value: dict, ticker: str | None = None) -> dict:
    if not isinstance(value, dict):
        raise ValueError('event context must be an object')
    required = {'ticker', 'period', 'basis', 'source_url', 'source_quote', 'reviewed'}
    if set(value) != required or value['reviewed'] is not True:
        raise ValueError('event context requires ticker, period, basis, source_url, source_quote and reviewed=true')
    if not all(isinstance(value[k], str) for k in required - {'reviewed'}):
        raise ValueError('event context text fields must be strings')
    if not re.fullmatch(r'[A-Z][A-Z0-9.-]{0,9}', value['ticker']) or (ticker and ticker != value['ticker']):
        raise ValueError('event context ticker mismatch')
    if not re.fullmatch(r'20\d{2}Q[1-4]', value['period']) or value['basis'] not in {'fiscal', 'calendar'}:
        raise ValueError('event context needs an explicit 2000-2099 quarter and fiscal/calendar basis')
    u = urlsplit(value['source_url'])
    if u.scheme != 'https' or not u.hostname or u.username or u.password or len(value['source_url']) > 2000:
        raise ValueError('event source must be a bounded HTTPS reference; it is not fetched automatically')
    if not 1 <= len(value['source_quote']) <= 2000:
        raise ValueError('event source quote must be 1-2000 characters')
    if (value['basis'] == 'calendar' and re.search(r'\bfiscal\b|\bFY\s*20', value['source_quote'], re.I)) or (value['basis'] == 'fiscal' and re.search(r'\bcalendar\b', value['source_quote'], re.I)):
        raise ValueError('event source quote conflicts with fiscal/calendar basis')
    periods = period_mentions(value['source_quote'])
    if not periods or any(m['period'] != value['period'] or m['basis'] not in (None, value['basis']) for m in periods):
        raise ValueError('event source quote must identify exactly the declared period and compatible basis')
    return dict(value)


def bind_event_period(claim: str, quote: str, ticker: str | None, context: dict | None) -> tuple[str, dict | None]:
    if not context or ticker != context['ticker'] or missing_period_reason(claim) is None:
        return claim, None
    # Require an actual current-quarter reference in both source and rewrite.
    # Historical comparisons, guidance and mixed timing are not filled in.
    relative = re.compile(r'\bthis quarter\b', re.I)
    conflict = re.compile(r'\b(?:last|previous|next|prior)\s+(?:quarter|year)|\byear.to.date\b', re.I)
    if not relative.search(quote) or not relative.search(claim) or conflict.search(quote + ' ' + claim):
        return claim, None
    if period_mentions(quote):
        return claim, None
    p = context['period'];label = f"{context['basis']} Q{p[-1]} {p[:4]}"
    bound = relative.sub(label, claim)
    return bound, {'kind': 'reviewed_event_metadata', 'authenticated': False,
                   'conditional_on_context': True, 'context': dict(context),
                   'note': 'Period supplied separately; not spoken text, issuer authentication or financial evidence.'}


def fiscal_header_bindings(claim: str, post: str, context: dict | None) -> list[dict]:
    """Resolve a short FY header only with an explicit matching full-year anchor.

    No century inference, no prior-year inference and no column/value alignment
    assertion. Each header occurrence remains available for review.
    """
    anchors = period_mentions(post)
    if context:
        anchors += [{'period': context['period'], 'basis': context['basis'], 'event_context': dict(context), 'authenticated': False}]
    bindings = []
    for m in re.finditer(r'\bFY\s*(\d{2})\s+Q([1-4])\b', claim, re.I):
        headers = list(re.finditer(r'\bFY\s*'+m[1]+r'\s+Q'+m[2]+r'\b', post, re.I))
        matches = {a['period'] for a in anchors if a['basis'] == 'fiscal' and a['period'].endswith(m[1]+'Q'+m[2])}
        if not headers or len(matches) != 1:
            continue
        period = next(iter(matches))
        bindings.append({'claim_span': list(m.span()), 'text': m[0], 'period': period,
                         'header_spans': [list(h.span()) for h in headers],
                         'basis': 'fiscal', 'anchor': 'document or reviewed event metadata',
                         'column_alignment_verified': False,
                         'full_year_anchors': [a for a in anchors if a['period'] == period and a['basis'] == 'fiscal']})
    return bindings
