"""Pure parsing helpers for the number phrase in a financial claim."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import NamedTuple


class ParsedNumber(NamedTuple):
    """A number in base units and the rounding precision implied by its text."""

    value: float
    precision: float


_NUMBER_PATTERN = re.compile(
    r"""
    (?P<sign>[+-])?
    \s*
    (?P<currency>[$€£])?
    \s*
    (?P<number>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)
    \s*
    (?P<unit>
        trillion|trillions|tn|t|
        billion|billions|bn|b|
        million|millions|mn|m|
        thousand|thousands|k|
        percent|%
    )?
    (?![A-Za-z0-9])
    """,
    re.IGNORECASE | re.VERBOSE,
)

_UNIT_MULTIPLIERS = {
    "thousand": 1e3,
    "thousands": 1e3,
    "k": 1e3,
    "million": 1e6,
    "millions": 1e6,
    "mn": 1e6,
    "m": 1e6,
    "billion": 1e9,
    "billions": 1e9,
    "bn": 1e9,
    "b": 1e9,
    "trillion": 1e12,
    "trillions": 1e12,
    "tn": 1e12,
    "t": 1e12,
}


def _decimal_places(raw_number: str) -> int:
    mantissa = raw_number.replace(",", "")
    if "." not in mantissa:
        return 0
    return len(mantissa.partition(".")[2])


def _candidate_score(match: re.Match[str]) -> int:
    unit = (match.group("unit") or "").lower()
    has_marker = bool(match.group("currency") or unit)
    if unit in {"%", "percent"}:
        return 4
    if unit:
        return 3
    if match.group("currency"):
        return 2
    return 1 if not has_marker else 0


def parse_stated_number(stated_text: str) -> ParsedNumber | None:
    """Parse a claim's number phrase into ``(value, precision)``.

    The parser deliberately returns magnitudes.  Words such as ``loss`` do not
    make a number negative; the model's claim type and stated value carry the
    sign.  Percentages are returned as percentage points, so ``22%`` becomes
    ``22.0`` rather than ``0.22``.
    """

    if not isinstance(stated_text, str) or not stated_text.strip():
        return None
    matches = list(_NUMBER_PATTERN.finditer(stated_text))
    if not matches:
        return None

    # A phrase copied from a full claim can contain years or quarter numbers.
    # Prefer a currency, scale, or percentage marker; if there is no marker,
    # the last number is usually the asserted amount rather than a date.
    marked = [match for match in matches if _candidate_score(match) > 1]
    if marked:
        selected = max(marked, key=lambda match: (_candidate_score(match), -match.start()))
    else:
        selected = matches[-1]

    raw_number = selected.group("number")
    try:
        mantissa = abs(Decimal(raw_number.replace(",", "")))
    except InvalidOperation:
        return None

    unit = (selected.group("unit") or "").lower()
    multiplier = _UNIT_MULTIPLIERS.get(unit, 1.0)
    try:
        value = mantissa * Decimal(str(multiplier))
        place = Decimal(1).scaleb(-_decimal_places(raw_number))
        precision = (place * Decimal(str(multiplier))) / Decimal(2)
    except (InvalidOperation, ValueError):
        return None
    return ParsedNumber(float(value), float(precision))


# Small aliases keep the pure helper discoverable for callers that describe the
# operation as parsing a number rather than parsing stated text.
parse_number = parse_stated_number
parse_stated_text = parse_stated_number


__all__ = [
    "ParsedNumber",
    "parse_number",
    "parse_stated_number",
    "parse_stated_text",
]
