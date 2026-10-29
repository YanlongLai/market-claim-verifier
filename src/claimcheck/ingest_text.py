"""Conservative, source-mapped number normalization for heard/read text.

No evidence, model guesses or issuer data enter this module. Unsupported word
sequences stay verbatim; units and period words are never inferred.
"""
from __future__ import annotations

import re
from typing import Any

ONES = dict(zip("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split(), range(20)))
TENS = dict(zip("twenty thirty forty fifty sixty seventy eighty ninety".split(), range(20, 100, 10)))
JOINED = {a + b: [a, b] for a in TENS for b, n in ONES.items() if 0 < n < 10}
WORDS = set(ONES) | set(TENS) | set(JOINED) | {"hundred", "thousand", "point", "and", "negative", "minus"}
_WORD = "(?:" + "|".join(sorted(WORDS, key=len, reverse=True)) + ")"
NUMBER_WORDS = re.compile(r"\b" + _WORD + r"(?:[\s-]+" + _WORD + r")*\b", re.I)
GROUPED = re.compile(r"(?<![\w.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\w|,\d|\.\d)")
QUARTERS = re.compile(r"\b(first|second|third|fourth)[ -]+quarter\b", re.I)


def _small(words: list[str]) -> int | None:
    if not words:
        return 0
    prefix = 0
    if len(words) >= 2 and words[0] in ONES and 1 <= ONES[words[0]] <= 9 and words[1] == "hundred":
        prefix, words = ONES[words[0]] * 100, words[2:]
        if words[:1] == ["and"]:
            words = words[1:]
    if not words:
        return prefix
    if len(words) == 1 and words[0] in ONES:
        return prefix + ONES[words[0]]
    if words[0] in TENS and (len(words) == 1 or len(words) == 2 and words[1] in ONES and 0 < ONES[words[1]] < 10):
        return prefix + TENS[words[0]] + (ONES[words[1]] if len(words) == 2 else 0)
    return None


def word_number(raw: str) -> str | None:
    words = []
    for word in re.split(r"[\s-]+", raw.lower()):
        words.extend(JOINED.get(word, [word]))
    sign = ""
    if words[:1] in (["minus"], ["negative"]):
        sign, words = "-", words[1:]
    if not words or words.count("point") > 1 or words.count("thousand") > 1:
        return None
    decimals: list[str] = []
    if "point" in words:
        p = words.index("point")
        decimals, words = words[p + 1:], words[:p]
        if not decimals or any(w not in ONES or ONES[w] > 9 for w in decimals):
            return None
    if "thousand" in words:
        p = words.index("thousand")
        high, tail = _small(words[:p]), words[p + 1:]
        if tail[:1] == ["and"]:
            tail = tail[1:]
        low = _small(tail)
        value = high * 1000 + low if high and low is not None else None
    else:
        value = _small(words) if words else (0 if decimals else None)
    if value is None:
        return None
    return sign + str(value) + ("." + "".join(str(ONES[w]) for w in decimals) if decimals else "")


def normalize_numbers(text: str) -> tuple[str, list[dict[str, Any]]]:
    replacements = [(m.start(), m.end(), "Q" + str(["first", "second", "third", "fourth"].index(m[1].lower()) + 1))
                    for m in QUARTERS.finditer(text)]
    for match in NUMBER_WORDS.finditer(text):
        # Keep "a hundred and twelve" together, but split sentence conjunctions
        # such as "fortytwo and twelve percent" and leading/trailing "and".
        raw, chunks, cursor = match[0], [], 0
        for conjunction in re.finditer(r"\band\b", raw, re.I):
            if re.search(r"\b(?:hundred|thousand)[\s-]*$", raw[cursor:conjunction.start()], re.I) and raw[conjunction.end():].strip():
                continue
            chunks.append((cursor, conjunction.start()))
            cursor = conjunction.end()
        chunks.append((cursor, len(raw)))
        for a, b in chunks:
            piece = raw[a:b].strip(" -\t\r\n")
            start = match.start() + a + len(raw[a:b]) - len(raw[a:b].lstrip(" -\t\r\n"))
            value = word_number(piece)
            if value is not None and piece:
                replacements.append((start, start + len(piece), value))
    replacements += [(m.start(), m.end(), m[0].replace(",", "")) for m in GROUPED.finditer(text)]
    parts, edits, cursor, length = [], [], 0, 0
    for start, end, value in sorted(replacements):
        parts.append(text[cursor:start])
        length += start - cursor
        edits.append({"raw_span": [start, end], "normalized_span": [length, length + len(value)],
                      "heard_or_read": text[start:end], "normalized": value})
        parts.append(value)
        length += len(value)
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts), edits


def original_offset(offset: int, edits: list[dict[str, Any]], *, end: bool = False) -> int:
    """Map a normalized boundary back to source; a replaced word is indivisible."""
    delta = 0
    for edit in edits:
        a, b = edit["normalized_span"]
        x, y = edit["raw_span"]
        if offset <= a:
            break
        if offset < b:
            return y if end else x
        delta += (b - a) - (y - x)
    return offset - delta
