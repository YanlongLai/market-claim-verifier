"""Deterministic HTML text, table coordinates, period labels and numeric tokens.

Offsets are Python character offsets into the normalized text (not HTML bytes).
Whitespace is collapsed within a block/cell; blocks use LF and cells use ` | `.
No model participates in extraction.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from html.parser import HTMLParser
from typing import Any


@dataclass
class Node:
    tag: str
    attrs: dict[str, str | None] = field(default_factory=dict)
    children: list[Any] = field(default_factory=list)


class _HTML(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def _hidden(node: Node) -> bool:
    return node.tag in {"head", "script", "style", "noscript", "ix:hidden"} or "hidden" in node.attrs or bool(
        re.search(r"display\s*:\s*none|visibility\s*:\s*hidden", node.attrs.get("style") or "", re.I))


def _plain(node: Any) -> str:
    if isinstance(node, str):
        return node
    if _hidden(node):
        return ""
    if node.tag == "br":
        return " "
    return "".join(_plain(child) for child in node.children)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Document:
    text: str
    spans: list[dict[str, Any]]


def parse_html(raw: bytes | str) -> Document:
    parser = _HTML()
    parser.feed(raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw)
    spans: list[dict[str, Any]] = []
    lines: list[str] = []
    offset, table_counter = 0, 0
    occupied: dict[int | None, dict[int, int]] = {}
    blocks = {"p", "div", "li", "ul", "ol", "table", "tr", "h1", "h2", "h3", "h4", "h5", "section", "blockquote", "center"}

    def add(text: str, table: int | None = None, cells: list[dict[str, Any]] | None = None) -> None:
        nonlocal offset
        if not text:
            return
        span = {"text": text, "start": offset, "end": offset + len(text),
                "kind": "table_row" if cells is not None else "text", "table": table}
        if cells is not None:
            span["cells"] = [{**cell, "start": offset + cell["start"], "end": offset + cell["end"]} for cell in cells]
        spans.append(span)
        lines.append(text)
        offset += len(text) + 1

    def contains(node: Node, tag: str) -> bool:
        return any(isinstance(c, Node) and (c.tag == tag or contains(c, tag)) for c in node.children)

    def walk(node: Any, table: int | None = None) -> None:
        nonlocal table_counter
        if isinstance(node, str):
            add(clean(node), table)
            return
        if _hidden(node):
            return
        if node.tag == "table":
            table_counter += 1
            table = table_counter
        if node.tag == "tr" and not contains(node, "table"):
            cells, col, cursor = [], 0, 0
            blocked = occupied.get(table, {})
            next_blocked = {c: n - 1 for c, n in blocked.items() if n > 1}
            for cell in node.children:
                if not isinstance(cell, Node) or cell.tag not in {"td", "th"}:
                    continue
                text = clean(_plain(cell))
                width = min(100, max(1, int(cell.attrs.get("colspan") or 1)))
                height = min(100, max(1, int(cell.attrs.get("rowspan") or 1)))
                while any(c in blocked for c in range(col, col + width)):
                    col += 1
                cells.append({"text": text, "column": col, "colspan": width,
                              "rowspan": height,
                              "start": cursor, "end": cursor + len(text)})
                if height > 1:
                    next_blocked.update({c: height - 1 for c in range(col, col + width)})
                col += width
                cursor += len(text) + 3
            if cells:
                add(" | ".join(c["text"] for c in cells), table, cells)
            occupied[table] = next_blocked
            return
        pending: list[str] = []
        for child in node.children:
            if isinstance(child, Node) and (child.tag in blocks or any(contains(child, t) for t in ("p", "table", "div"))):
                add(clean("".join(pending)), table)
                pending = []
                walk(child, table)
            else:
                pending.append(_plain(child))
        add(clean("".join(pending)), table)

    walk(parser.root)
    return Document("\n".join(lines), spans)


ORDINAL = {"first": 1, "second": 2, "third": 3, "fourth": 4, "1st": 1, "2nd": 2, "3rd": 3, "4th": 4}
_Q = r"(?:(?:first|second|third|fourth|1st|2nd|3rd|4th)[ -]+quarter|q[1-4])"


def period_labels(text: str, *, context: str | None = None) -> set[str]:
    """Read explicit issuer fiscal labels. Calendar aliases need separate proof.

    An ordinal outlook with no year may inherit the release's explicit fiscal
    year, rolling Q4 -> Q1 forward. Date-only columns stay dates until tied to
    an explicit release reporting period.
    """
    text = text.lower()
    result: set[str] = set()
    patterns = [rf"(?P<q>{_Q})(?:\s+of)?\s+(?:(?:fiscal(?:\s+year)?|fy)\s*)?(?P<y>20\d{{2}})",
                rf"(?:fiscal(?:\s+year)?\s*|fy\s*)?(?P<y>20\d{{2}})[ -]+(?P<q>{_Q})"]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            qtext = match["q"]
            quarter = int(qtext[-1]) if qtext.startswith("q") else ORDINAL[qtext.split("quarter")[0].strip(" -")]
            result.add(f"FY{match['y']}Q{quarter}")
    if not result and context and (match := re.fullmatch(r"FY(20\d{2})Q([1-4])", context)):
        quarters = re.findall(_Q, text)
        for qtext in quarters:
            q = int(qtext[-1]) if qtext.startswith("q") else ORDINAL[qtext.split("quarter")[0].strip(" -")]
            y = int(match[1]) + (1 if int(match[2]) == 4 and q == 1 else 0)
            result.add(f"FY{y}Q{q}")
    # A fiscal year mentioned alongside a quarter is generally that quarter's
    # year, not a separate annual column. Annual-only headings are unambiguous.
    if not re.search(_Q, text):
        for match in re.finditer(r"(?:fiscal\s+(?:year\s+)?|full[ -]year\s+|fy\s*)(20\d{2})", text):
            result.add(f"FY{match[1]}")
    return result


def date_labels(text: str) -> list[str]:
    months = r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
    dates = []
    for match in re.finditer(rf"\b({months})\.?\s+(\d{{1,2}}),?\s+(20\d{{2}})\b", text, re.I):
        try:
            dates.append(datetime.strptime(f"{match[1][:3]} {match[2]} {match[3]}", "%b %d %Y").date().isoformat())
        except ValueError:
            pass
    return dates


SCALE = {"thousand": Decimal(1000), "million": Decimal(1000000), "billion": Decimal(1000000000)}
_NUMBER = r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
_RANGE = re.compile(rf"(?P<a>\(?-?\$?\s*{_NUMBER}\)?)(?:\s*(?P<sa>thousand|million|billion))?\s*(?:-|–|—|\bto\b|\band\b)\s*(?P<b>\(?\$?\s*{_NUMBER}\)?)(?:\s*(?P<sb>thousand|million|billion))?\s*(?P<pct>%|percent)?", re.I)
_POINT = re.compile(rf"(?P<a>\(?\$?\s*{_NUMBER}\)?)(?:\s*(?P<sa>thousand|million|billion))?\s*(?P<pct>%|percent)?", re.I)


def _decimal(raw: str) -> Decimal:
    raw = raw.strip().replace("$", "").replace(",", "").replace(" ", "")
    return -Decimal(raw[1:-1]) if raw.startswith("(") and raw.endswith(")") else Decimal(raw)


def number(text: str, *, scale: Decimal = Decimal(1), per_share: bool = False) -> dict[str, Any] | None:
    """Parse one point/range and a literal +/- money or percentage tolerance.

    Verbal ranges deliberately have no numeric mapping. Callers must isolate
    the metric's value before calling; years are not financial values.
    """
    if re.search(r"(?:single|double)[ -]digits?|\b(?:low|mid|high)[ -](?:\d|teens)", text, re.I):
        return None
    match = _RANGE.search(text) or _POINT.search(text)
    if not match:
        return None
    a_scale = SCALE.get((match["sa"] or "").lower())
    b_scale = SCALE.get((match.groupdict().get("sb") or "").lower())
    multiplier = Decimal(1) if per_share or match["pct"] else scale
    lo = _decimal(match["a"]) * (a_scale or b_scale or multiplier)
    b = match.groupdict().get("b")
    hi = _decimal(b) * (b_scale or a_scale or multiplier) if b else lo
    center = None
    suffix = text[match.end():]
    if not b and (pm := re.search(r"(?:plus\s+or\s+minus|\+/-|±)\s*(.*)", suffix, re.I)):
        delta = _POINT.match(pm[1])
        if not delta:
            return None
        center = lo
        amount = _decimal(delta["a"])
        width = abs(lo) * amount / 100 if delta["pct"] else amount * SCALE.get((delta["sa"] or "").lower(), multiplier)
        lo, hi = lo - width, lo + width
    if lo > hi:
        return None
    return {"low": float(lo), "high": float(hi), "center": float(center) if center is not None else None,
            "unit": "percent" if match["pct"] else "USD/shares" if per_share else "USD",
            "number_start": match.start(), "number_end": match.end(), "literal": match[0].strip()}
