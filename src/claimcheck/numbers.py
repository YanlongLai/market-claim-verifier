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

# These phrases are deliberately kept small and literal.  The program uses
# the words immediately before a number, rather than trusting a model's
# comparator field.  In particular, ``nearly`` and ``almost`` are treated as
# ordinary approximation language; we do not attempt to model their semantic
# difference from ``about``.
_COMPARATOR_NUMBER = (
    r"(?:[$€£]\s*)?(?:\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?|\.\d+)"
    r"(?:\s*(?:trillion|trillions|tn|t|billion|billions|bn|b|million|"
    r"millions|mn|m|thousand|thousands|k|percent|%))?"
)
_COMPARATOR_PHRASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "approx",
        (
            r"about",
            r"around",
            r"roughly",
            r"approximately",
            r"nearly",
            r"almost",
            r"close\s+to",
            r"some",
            r"~",
        ),
    ),
    ("gte", (r"at\s+least", r"no\s+less\s+than")),
    ("lte", (r"at\s+most", r"no\s+more\s+than", r"up\s+to")),
    ("gt", (r"topped", r"exceeded", r"above", r"more\s+than", r"over", r"surpassed", r"beat")),
    ("lt", (r"below", r"under", r"less\s+than", r"short\s+of")),
)


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


_MULTIPLIER_WORDS = (("double", 100), ("doubled", 100), ("doubling", 100), ("twice", 100), ("triple", 200),
                     ("tripled", 200), ("tripling", 200), ("quadruple", 300), ("quadrupled", 300))
_MULTIPLIER_PATTERN = re.compile(
    r"(?P<hedge>\b(?:more than|over|at least|nearly|almost|about|roughly|less than|under)\s+)?"
    r"\b(?P<word>" + "|".join(word for word, _ in _MULTIPLIER_WORDS) + r")\b",
    re.IGNORECASE,
)


def multiplier_words_to_percent(text: str) -> str:
    """Rewrite growth multipliers as percent growth: "more than double" -> "more than 100%".

    A bare "doubled" becomes "about 100%": in prose it rarely means exactly 100.0% growth.
    """

    growth = {word: pct for word, pct in _MULTIPLIER_WORDS}

    def repl(match: re.Match[str]) -> str:
        hedge = match.group("hedge") or "about "
        return f"{hedge}{growth[match.group('word').lower()]}%"

    return _MULTIPLIER_PATTERN.sub(repl, text or "")


def parse_stated_number(stated_text: str) -> ParsedNumber | None:
    """Parse a claim's number phrase into ``(value, precision)``.

    The parser deliberately returns magnitudes.  Words such as ``loss`` do not
    make a number negative; the model's claim type and stated value carry the
    sign.  Percentages are returned as percentage points, so ``22%`` becomes
    ``22.0`` rather than ``0.22``.
    """

    if not isinstance(stated_text, str) or not stated_text.strip():
        return None
    original_text = stated_text
    growth_word = _MULTIPLIER_PATTERN.search(stated_text)
    stated_text = multiplier_words_to_percent(stated_text)
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
    if growth_word is not None and not re.search(r"\d", original_text):
        # "doubled" is a rough multiple: accept growth within 15% of the implied rate (100% -> 85-115%).
        precision = Decimal(str(float(value))) * Decimal("0.15") / Decimal(2)
    return ParsedNumber(float(value), float(precision))


def _phrase_precedes_number(
    text: str, phrase: str, target_value: float | None = None
) -> bool:
    """Return whether a comparator phrase is attached to a number."""

    # ``the`` and ``a`` cover common prose such as "more than the $100B
    # threshold" without allowing an arbitrary sentence-wide match.
    pattern = re.compile(
        rf"(?<![a-z])(?:{phrase})(?![a-z])"
        rf"(?:\s+(?:a|an|the))?\s*(?P<number>{_COMPARATOR_NUMBER})",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        if target_value is None:
            return True
        parsed = parse_stated_number(match.group("number"))
        if parsed is not None and parsed.value == target_value:
            return True
    return False


def infer_comparator(
    stated_text: str | None = "",
    sub_claim_text: str | None = "",
    original_claim: str | None = "",
) -> str:
    """Infer the program comparator from the wording around the number.

    The search considers the literal ``stated_text``, the sub-claim text, and
    an optional original-claim sentence.  If no listed hedge or inequality
    phrase is attached to a number, the comparator is ``eq``.  ``nearly`` and
    ``almost`` intentionally map to ``approx`` as a simple, conservative rule.
    """

    texts = [
        multiplier_words_to_percent(value.strip().replace("≈", "~"))
        for value in (stated_text, sub_claim_text, original_claim)
        if isinstance(value, str) and value.strip()
    ]
    if not texts:
        return "eq"

    # The literal stated_text is the closest available span.  A broader
    # sub-claim/original sentence is still consulted for inequality words such
    # as "exceeded" when the model supplied only the number as stated_text.
    for comparator, phrases in _COMPARATOR_PHRASES:
        if any(_phrase_precedes_number(texts[0], phrase) for phrase in phrases):
            return comparator
    stated_numbers = list(
        re.finditer(_COMPARATOR_NUMBER, texts[0], flags=re.IGNORECASE)
    )
    parsed_stated = (
        parse_stated_number(stated_numbers[-1].group(0))
        if stated_numbers
        else parse_stated_number(texts[0])
    )
    target_value = parsed_stated.value if parsed_stated is not None else None
    for comparator, phrases in _COMPARATOR_PHRASES[1:]:
        if any(
            _phrase_precedes_number(text, phrase, target_value)
            for text in texts[1:]
            for phrase in phrases
        ):
            return comparator

    for text in texts[1:]:
        for phrase in _COMPARATOR_PHRASES[0][1]:
            if _phrase_precedes_number(text, phrase, target_value):
                return "approx"
    return "eq"


# Descriptive aliases keep the pure helper easy to discover for callers and
# older integrations that use a noun-first name.
comparator_from_text = infer_comparator
infer_claim_comparator = infer_comparator


# Small aliases keep the pure helper discoverable for callers that describe the
# operation as parsing a number rather than parsing stated text.
parse_number = parse_stated_number
parse_stated_text = parse_stated_number


__all__ = [
    "ParsedNumber",
    "comparator_from_text",
    "infer_claim_comparator",
    "infer_comparator",
    "parse_number",
    "parse_stated_number",
    "parse_stated_text",
]
