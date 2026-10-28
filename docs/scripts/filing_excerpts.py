"""Find the exact inline-XBRL passage behind a verified evidence fact.

The parser in this module deliberately works on the small, stable subset of
inline XBRL that the site needs.  It keeps the SEC download code separate from
the pure HTML/context/fact matching functions so the latter can be tested
offline with tiny filing fragments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import hashlib
import json
import re
from pathlib import Path
import time
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen


SEC_HOSTS = {"www.sec.gov", "sec.gov", "data.sec.gov"}
SEC_USER_AGENT = "DappGo market-claim-verifier admin@dappgo.com"
REQUEST_INTERVAL_SECONDS = 0.2


def _local_name(value: str) -> str:
    return value.rsplit(":", 1)[-1].lower()


def _collapse_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    parent: "_Node | None" = None
    children: list["_Node"] = field(default_factory=list)
    text: str | None = None
    order: int = -1


class _DocumentParser(HTMLParser):
    _VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("root")
        self.stack: list[_Node] = [self.root]

    def _attributes(self, attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        result: dict[str, str] = {}
        for key, value in attrs:
            if value is not None:
                result[_local_name(key)] = value
        return result

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(_local_name(tag), self._attributes(attrs), self.stack[-1])
        self.stack[-1].children.append(node)
        if node.tag not in self._VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(_local_name(tag), self._attributes(attrs), self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag: str) -> None:
        target = _local_name(tag)
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == target:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(_Node("#text", parent=self.stack[-1], text=data))


def _parse_document(html: str) -> _Node:
    parser = _DocumentParser()
    parser.feed(html)
    parser.close()
    order = 0
    for node in _walk(parser.root):
        node.order = order
        order += 1
    return parser.root


def _walk(node: _Node) -> Iterable[_Node]:
    yield node
    for child in node.children:
        yield from _walk(child)


def _text_content(node: _Node) -> str:
    if node.tag == "#text":
        return node.text or ""
    parts = [_text_content(child) for child in node.children]
    if node.tag in {"div", "span", "p", "li", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6"}:
        return " ".join(part for part in parts if part)
    return "".join(parts)


def _element_text(node: _Node) -> str:
    return _collapse_text(_text_content(node))


def _ancestor(node: _Node | None, tag: str) -> _Node | None:
    current = node.parent if node else None
    while current is not None:
        if current.tag == tag:
            return current
        current = current.parent
    return None


def _has_ancestor(node: _Node, ancestor: _Node) -> bool:
    current: _Node | None = node.parent
    while current is not None:
        if current is ancestor:
            return True
        current = current.parent
    return False


def _first_descendant(node: _Node, tags: set[str]) -> _Node | None:
    for child in _walk(node):
        if child is not node and child.tag in tags:
            return child
    return None


def _number(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _parse_fact_value(raw: str, scale: str | None, sign: str | None) -> Decimal | None:
    cleaned = _collapse_text(raw).replace(",", "").replace("$", "").replace("€", "").replace("£", "")
    if not cleaned or cleaned in {"-", "—", "–", "n/a", "na"}:
        return None

    negative_parentheses = cleaned.startswith("(") and cleaned.endswith(")")
    if negative_parentheses:
        cleaned = cleaned[1:-1].strip()
    cleaned = cleaned.rstrip("%")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None

    if negative_parentheses:
        value = -abs(value)
    if sign == "-":
        value = -abs(value)
    if scale and scale.lower() not in {"", "none"}:
        try:
            value *= Decimal(10) ** int(scale)
        except (ValueError, InvalidOperation):
            return None
    return value


def _decimal_json(value: Decimal | None) -> int | float | None:
    if value is None:
        return None
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _context_info(context: _Node) -> dict[str, Any]:
    start = _first_descendant(context, {"startdate"})
    end = _first_descendant(context, {"enddate"})
    instant = _first_descendant(context, {"instant"})
    return {
        "id": context.attrs.get("id"),
        "start": _element_text(start) if start else None,
        "end": _element_text(end) if end else None,
        "instant": _element_text(instant) if instant else None,
        "has_segment": any(child.tag == "segment" for child in _walk(context)),
    }


def parse_contexts(html: str) -> dict[str, dict[str, Any]]:
    """Return inline-XBRL contexts keyed by context id."""

    root = _parse_document(html)
    contexts: dict[str, dict[str, Any]] = {}
    for node in _walk(root):
        if node.tag != "context":
            continue
        info = _context_info(node)
        if info["id"]:
            contexts[str(info["id"])] = info
    return contexts


@dataclass
class _Fact:
    node: _Node
    name: str
    context_ref: str | None
    fact_id: str | None
    raw_value: str
    parsed_value: Decimal | None
    scale: int
    sign: str | None

    @property
    def table(self) -> _Node | None:
        return _ancestor(self.node, "table")

    @property
    def row(self) -> _Node | None:
        return _ancestor(self.node, "tr")


def _fact_nodes(root: _Node) -> list[_Fact]:
    facts: list[_Fact] = []
    for node in _walk(root):
        if node.tag != "nonfraction":
            continue
        raw_value = _element_text(node)
        scale_value = node.attrs.get("scale") or "0"
        try:
            scale = int(scale_value)
        except ValueError:
            scale = 0
        facts.append(
            _Fact(
                node=node,
                name=node.attrs.get("name", ""),
                context_ref=node.attrs.get("contextref"),
                fact_id=node.attrs.get("id"),
                raw_value=raw_value,
                parsed_value=_parse_fact_value(raw_value, scale_value, node.attrs.get("sign")),
                scale=scale,
                sign=node.attrs.get("sign"),
            )
        )
    return facts


def _expected_concept(evidence: Mapping[str, Any]) -> str | None:
    concept = evidence.get("concept")
    if not concept:
        return None
    concept_text = str(concept)
    return concept_text if ":" in concept_text else f"us-gaap:{concept_text}"


_REVENUE_CONCEPTS = (
    "us-gaap:Revenues",
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax",
)
REVENUE_EQUIVALENTS = {name: tuple(other for other in _REVENUE_CONCEPTS if other != name) for name in _REVENUE_CONCEPTS}


def _context_matches(context: Mapping[str, Any], evidence: Mapping[str, Any]) -> bool:
    if context.get("has_segment"):
        return False
    expected_start = evidence.get("start")
    expected_end = evidence.get("end")
    if expected_start and expected_end:
        return context.get("start") == expected_start and context.get("end") == expected_end
    if expected_end:
        observed_end = context.get("instant") or context.get("end")
        return observed_end == expected_end
    if expected_start:
        return context.get("start") == expected_start
    return True


def _matching_facts(root: _Node, evidence: Mapping[str, Any]) -> tuple[list[_Fact], str]:
    contexts = {
        key: _context_info(node)
        for node in _walk(root)
        if node.tag == "context" and node.attrs.get("id")
        for key in [str(node.attrs["id"])]
    }
    facts = _fact_nodes(root)
    concept = _expected_concept(evidence)
    target_value = _number(evidence.get("value"))
    if not concept:
        return [], "evidence is missing an XBRL concept"
    if target_value is None:
        return [], "evidence is missing a numeric value"

    concept_facts = [fact for fact in facts if fact.name == concept or fact.name in REVENUE_EQUIVALENTS.get(concept, ())]
    if not concept_facts:
        return [], f"no inline-XBRL fact named {concept}"

    context_facts = [
        fact
        for fact in concept_facts
        if fact.context_ref in contexts and _context_matches(contexts[fact.context_ref], evidence)
    ]
    if not context_facts:
        return [], "no consolidated context matches the evidence start/end dates"

    matching = [fact for fact in context_facts if fact.parsed_value == target_value]
    # Issuers tag total revenue with either concept; the statement line may use the other one (Tesla's income
    # statement uses RevenueFromContract..., its geographic note uses Revenues). Same value and same period only.
    equivalents = REVENUE_EQUIVALENTS.get(concept, ())
    matching += [
        fact
        for fact in facts
        if fact.name in equivalents
        and fact.context_ref in contexts
        and _context_matches(contexts[fact.context_ref], evidence)
        and fact.parsed_value == target_value
    ]
    if not matching:
        observed = ", ".join(str(_decimal_json(fact.parsed_value)) for fact in context_facts[:3])
        suffix = f" (observed {observed})" if observed else ""
        return [], f"concept/context matched, but the reported value did not match{suffix}"
    return matching, ""


def _cell_nodes(row: _Node, table: _Node) -> list[_Node]:
    cells: list[_Node] = []
    for node in _walk(row):
        if node.tag not in {"td", "th"}:
            continue
        if _ancestor(node, "tr") is row and _ancestor(node, "table") is table:
            cells.append(node)
    return cells


def _span(cell: _Node, attribute: str) -> int:
    try:
        return max(1, int(cell.attrs.get(attribute, "1")))
    except ValueError:
        return 1


def _positioned_cells(row: _Node, table: _Node) -> list[dict[str, Any]]:
    positioned: list[dict[str, Any]] = []
    column = 0
    for index, cell in enumerate(_cell_nodes(row, table)):
        colspan = _span(cell, "colspan")
        positioned.append(
            {
                "index": index,
                "node": cell,
                "text": _element_text(cell),
                "colspan": colspan,
                "column_start": column,
                "column_end": column + colspan,
            }
        )
        column += colspan
    return positioned


def _rows(table: _Node) -> list[_Node]:
    return [node for node in _walk(table) if node.tag == "tr" and _ancestor(node, "table") is table]


def _row_has_fact(row: _Node) -> bool:
    return any(node.tag == "nonfraction" and _ancestor(node, "tr") is row for node in _walk(row))


def _cell_for_fact(fact: _Fact, table: _Node) -> tuple[list[dict[str, Any]], int | None]:
    row = fact.row
    if row is None:
        return [], None
    positioned = _positioned_cells(row, table)
    for cell in positioned:
        if _has_ancestor(fact.node, cell["node"]) or fact.node is cell["node"]:
            return positioned, int(cell["index"])
    return positioned, None


def _nearest_preceding_section_title(root: _Node, table: _Node) -> str | None:
    def clean_title(text: str) -> str:
        # Some SEC filing templates split the word INCOME across two styled
        # spans.  Restore that word after the text-only extraction.
        return re.sub(r"\bINC\s+OME\b", "INCOME", text)

    candidates = [
        node
        for node in _walk(root)
        if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p"}
        and node.order < table.order
        and _ancestor(node, "table") is None
        and _element_text(node)
        # Page numbers ("92") and running sentences are not section titles.
        and re.search(r"[A-Za-z]{3}", _element_text(node))
        and len(_element_text(node)) <= 90
        and not _element_text(node).rstrip().endswith(".")
    ]
    if candidates:
        return clean_title(_element_text(candidates[-1]))

    # SEC filings often style section headings as a short uppercase div/span
    # instead of using a semantic h2.  Use that only as a fallback, and never
    # use an ancestor that contains the table itself.
    styled_candidates = []
    for node in _walk(root):
        if node.tag not in {"div", "span"} or node.order >= table.order or _ancestor(node, "table") is not None:
            continue
        text = _element_text(node)
        if not text or len(text) > 160 or _first_descendant(node, {"table"}) is not None:
            continue
        if text.startswith("(") and text.endswith(")"):
            continue
        if not re.search(r"[A-Za-z]{3}", text):  # page numbers such as "92"
            continue
        if len(text) > 90 or text.rstrip().endswith("."):  # a running sentence, not a heading
            continue
        if text.upper() == text or re.search(r"\b(statements?|operations|balance sheet|cash flows?|financial position|income)\b", text, re.I):
            styled_candidates.append(text)
    return clean_title(styled_candidates[-1]) if styled_candidates else None


def _fact_output(fact: _Fact, cell_index: int | None = None) -> dict[str, Any]:
    return {
        "id": fact.fact_id,
        "concept": fact.name,
        "raw_value": fact.raw_value,
        "scale": fact.scale,
        "sign": fact.sign,
        "full_value": _decimal_json(fact.parsed_value),
        "context_ref": fact.context_ref,
        "cell_index": cell_index,
    }


def _is_period_header(text: str) -> bool:
    """Return whether a header cell names a reporting period."""

    value = _collapse_text(text)
    if not value:
        return False
    return bool(
        re.search(r"\b(?:19|20)\d{2}\b", value)
        or re.search(r"\bQ[1-4]\b", value, re.IGNORECASE)
        or re.search(r"\bFY\b", value, re.IGNORECASE)
    )


def _join_compact_cell_texts(texts: Iterable[str]) -> str:
    """Join cell fragments without separating currency symbols from values."""

    joined = ""
    for raw_text in texts:
        text = _collapse_text(raw_text)
        if not text:
            continue
        if not joined:
            joined = text
            continue
        if text[0] in ",.%):;]" or joined[-1] in "$€£¥(":
            joined += text
        else:
            joined += f" {text}"
    return joined


def _compact_table(
    header_rows: list[dict[str, Any]],
    row_cells: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Collapse SEC spacer columns into the few logical columns a reader needs."""

    candidates: list[tuple[int, dict[str, Any], list[dict[str, Any]]]] = []
    for index, header in enumerate(header_rows):
        period_cells = [cell for cell in header.get("cells", []) if _is_period_header(cell.get("text", ""))]
        if len(period_cells) >= 2:
            candidates.append((len(period_cells), header, period_cells))
    if not candidates:
        return None

    _, period_header, period_cells = max(candidates, key=lambda candidate: (candidate[0], candidate[1].get("cells", [{}])[0].get("column_start", 0)))
    first_period_start = min(int(cell["column_start"]) for cell in period_cells)
    columns: list[dict[str, Any]] = [
        {
            "key": "label",
            "label": "",
            "column_start": 0,
            "column_end": first_period_start,
            "is_fact": False,
        }
    ]
    for period_cell in period_cells:
        columns.append(
            {
                "key": str(period_cell["text"]),
                "label": period_cell["text"],
                "column_start": int(period_cell["column_start"]),
                "column_end": int(period_cell["column_end"]),
                "is_fact": bool(period_cell.get("covers_fact")),
            }
        )

    compact_cells: list[dict[str, Any]] = []
    for column in columns:
        overlapping = [
            cell
            for cell in row_cells
            if int(cell["column_start"]) < column["column_end"]
            and int(cell["column_end"]) > column["column_start"]
        ]
        compact_cells.append(
            {
                "text": _join_compact_cell_texts(cell.get("text", "") for cell in overlapping),
                "is_fact": any(cell.get("is_fact") for cell in overlapping),
                "is_row_label": any(cell.get("is_row_label") for cell in overlapping),
            }
        )

    if not any(cell["text"] for cell in compact_cells):
        return None

    kept_columns: list[dict[str, Any]] = []
    kept_indices: list[int] = []
    for index, (column, cell) in enumerate(zip(columns, compact_cells)):
        if cell["text"] or cell["is_fact"] or cell["is_row_label"]:
            kept_columns.append(column)
            kept_indices.append(index)
    compact_cells = [compact_cells[index] for index in kept_indices]

    caption = next(
        (
            _collapse_text(cell.get("text", ""))
            for header in header_rows
            for cell in header.get("cells", [])
            if _collapse_text(cell.get("text", "")).startswith("(")
        ),
        None,
    )
    return {
        "caption": caption,
        "columns": kept_columns,
        "rows": [{"cells": compact_cells}] if any(cell["text"] for cell in compact_cells) else [],
        "period_header": [
            {
                "text": cell["text"],
                "column_start": cell["column_start"],
                "column_end": cell["column_end"],
                "is_fact": bool(cell.get("covers_fact")),
            }
            for cell in period_header.get("cells", [])
            if _is_period_header(cell.get("text", ""))
        ],
    }


def _table_excerpt(root: _Node, fact: _Fact) -> dict[str, Any] | None:
    table = fact.table
    row = fact.row
    if table is None or row is None:
        return None
    rows = _rows(table)
    row_index = next((index for index, candidate in enumerate(rows) if candidate is row), None)
    if row_index is None:
        return None
    positioned, fact_cell_index = _cell_for_fact(fact, table)
    if fact_cell_index is None:
        return None

    fact_cell = positioned[fact_cell_index]
    fact_column = int(fact_cell["column_start"])
    row_label_index = next(
        (
            int(cell["index"])
            for cell in positioned
            if cell["index"] != fact_cell_index
            and int(cell["column_end"]) <= int(fact_cell["column_start"])
            and cell["text"]
        ),
        None,
    )

    row_cells = []
    for cell in positioned:
        row_cells.append(
            {
                "text": cell["text"],
                "colspan": cell["colspan"],
                "column_start": cell["column_start"],
                "column_end": cell["column_end"],
                "is_fact": cell["index"] == fact_cell_index,
                "is_row_label": cell["index"] == row_label_index,
            }
        )

    header_rows = []
    header_cell_indices = []
    for header_index, header_row in enumerate(rows[:row_index]):
        if _row_has_fact(header_row):
            continue
        header_cells = []
        for cell in _positioned_cells(header_row, table):
            covers_fact = int(cell["column_start"]) <= fact_column < int(cell["column_end"])
            if covers_fact:
                header_cell_indices.append({"row_index": header_index, "cell_index": cell["index"]})
            header_cells.append(
                {
                    "text": cell["text"],
                    "colspan": cell["colspan"],
                    "column_start": cell["column_start"],
                    "column_end": cell["column_end"],
                    "covers_fact": covers_fact,
                }
            )
        if any(cell["text"] for cell in header_cells):
            header_rows.append({"cells": header_cells})

    compact = _compact_table(header_rows, row_cells)
    return {
        "type": "table",
        "section_title": _nearest_preceding_section_title(root, table),
        "headers": header_rows,
        "row": {
            "cells": row_cells,
            "fact_cell_index": fact_cell_index,
            "row_label_cell_index": row_label_index,
        },
        "fact": _fact_output(fact, fact_cell_index),
        "header_cell_indices": header_cell_indices,
        "compact": compact,
    }


def _raw_text_with_fact_offsets(node: _Node, fact_node: _Node) -> tuple[str, int, int]:
    pieces: list[str] = []
    fact_start: int | None = None
    fact_end: int | None = None

    def visit(current: _Node) -> None:
        nonlocal fact_start, fact_end
        if current is fact_node:
            fact_start = sum(len(piece) for piece in pieces)
        if current.tag == "#text":
            pieces.append(current.text or "")
        else:
            for child in current.children:
                visit(child)
        if current is fact_node:
            fact_end = sum(len(piece) for piece in pieces)

    visit(node)
    return "".join(pieces), fact_start or 0, fact_end if fact_end is not None else 0


def _normalize_with_mapping(raw: str) -> tuple[str, list[int]]:
    normalized: list[str] = []
    mapping: list[int] = [0] * len(raw)
    previous_space = False
    for index, character in enumerate(raw):
        if character.isspace():
            if normalized and not previous_space:
                normalized.append(" ")
            mapping[index] = max(0, len(normalized) - 1)
            previous_space = True
        else:
            normalized.append(character)
            mapping[index] = len(normalized) - 1
            previous_space = False
    text = "".join(normalized).strip()
    leading = len("".join(normalized)) - len("".join(normalized).lstrip())
    return text, [max(0, value - leading) for value in mapping]


def _trim_text_passage(text: str, fact_start: int, fact_end: int, limit: int = 400) -> tuple[str, int, int]:
    if len(text) <= limit:
        return text, fact_start, fact_end

    sentence_matches = list(re.finditer(r"[^.!?。！？]*[.!?。！？]", text))
    for match in sentence_matches:
        if match.start() <= fact_start < match.end() and len(match.group()) <= limit:
            sentence = match.group().strip()
            offset = match.start() + (len(match.group()) - len(match.group().lstrip()))
            return sentence, fact_start - offset, fact_end - offset

    half = (limit - (fact_end - fact_start)) // 2
    start = max(0, fact_start - half)
    end = min(len(text), start + limit)
    start = max(0, end - limit)
    while start < fact_start and start < len(text) and not text[start].isspace():
        start += 1
    while end > fact_end and end > 0 and end < len(text) and not text[end - 1].isspace():
        end -= 1
    passage = text[start:end].strip()
    left_trim = len(text[start:end]) - len(text[start:end].lstrip())
    return passage, fact_start - start - left_trim, fact_end - start - left_trim


def _text_excerpt(root: _Node, fact: _Fact) -> dict[str, Any]:
    block: _Node | None = None
    current: _Node | None = fact.node.parent
    while current is not None:
        if current.tag in {"p", "li", "blockquote", "div", "section", "article", "body"}:
            block = current
            if current.tag in {"p", "li", "blockquote"}:
                break
        current = current.parent
    block = block or root

    raw, raw_fact_start, raw_fact_end = _raw_text_with_fact_offsets(block, fact.node)
    text, mapping = _normalize_with_mapping(raw)
    first_nonspace = raw_fact_start
    while first_nonspace < raw_fact_end and raw[first_nonspace].isspace():
        first_nonspace += 1
    last_nonspace = raw_fact_end
    while last_nonspace > first_nonspace and raw[last_nonspace - 1].isspace():
        last_nonspace -= 1
    fact_start = mapping[first_nonspace] if first_nonspace < len(mapping) else 0
    fact_end = mapping[last_nonspace - 1] + 1 if last_nonspace > first_nonspace else fact_start
    passage, passage_start, passage_end = _trim_text_passage(text, fact_start, fact_end)

    preceding = [
        node
        for node in _walk(root)
        if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}
        and node.order < block.order
        and _element_text(node)
    ]
    return {
        "type": "text",
        "section_title": _element_text(preceding[-1]) if preceding else None,
        "text": passage,
        "fact_range": {"start": max(0, passage_start), "end": max(0, passage_end)},
        "fact": _fact_output(fact),
    }


def extract_filing_excerpt(html: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Match one evidence item and return a JSON-serializable excerpt result."""

    root = _parse_document(html)
    matching, reason = _matching_facts(root, evidence)
    if not matching:
        return {"matched": False, "excerpt": None, "reason": reason}

    table_matches = [fact for fact in matching if fact.table is not None and fact.row is not None]
    # The same number often appears in several tables (statements, notes, segment tables). Prefer the primary
    # financial statement, then the earliest table, so the passage reads as "Consolidated Statements of ...".
    def statement_rank(candidate: _Fact) -> int:
        title = _nearest_preceding_section_title(root, candidate.table) or ""
        return 0 if re.search(r"\bstatements?\b", title, re.I) else 1

    table_matches.sort(key=statement_rank)
    fact = table_matches[0] if table_matches else matching[0]
    excerpt = _table_excerpt(root, fact) if fact.table is not None else None
    if excerpt is None:
        excerpt = _text_excerpt(root, fact)
    return {"matched": True, "excerpt": excerpt, "reason": None}


# A short alias keeps the pure parsing entry point easy to discover in tests.
parse_inline_xbrl = extract_filing_excerpt


def _safe_host(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in SEC_HOSTS:
        raise ValueError(f"SEC filing fetch blocked for non-SEC URL: {url}")
    return host


def _cache_name(url: str) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix not in {".json", ".htm", ".html", ".xml"}:
        suffix = ".txt"
    return hashlib.sha256(url.encode("utf-8")).hexdigest() + suffix


def _accession_parts(evidence: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    accession = evidence.get("accn") or evidence.get("accession")
    filing_url = str(evidence.get("filing_url") or "")
    parsed = urlparse(filing_url)
    parts = [part for part in parsed.path.split("/") if part]
    cik: str | None = None
    accn_nodash: str | None = None
    if "data" in parts:
        data_index = parts.index("data")
        if len(parts) > data_index + 1:
            cik = parts[data_index + 1]
        if len(parts) > data_index + 2:
            accn_nodash = parts[data_index + 2].split(".", 1)[0]
    if accession:
        accession_text = str(accession)
        accession_nodash = re.sub(r"[^0-9]", "", accession_text)
        if len(accession_nodash) >= 10:
            accn_nodash = accession_nodash
    return str(accession) if accession else None, cik, accn_nodash


def _filing_folder_url(evidence: Mapping[str, Any]) -> str | None:
    filing_url = str(evidence.get("filing_url") or "").rstrip("/")
    if not filing_url:
        return None
    _safe_host(filing_url)
    parsed = urlparse(filing_url)
    if parsed.path.lower().endswith(".htm") or parsed.path.lower().endswith(".html"):
        return filing_url.rsplit("/", 1)[0]
    return filing_url


def _select_primary_document(index_data: Mapping[str, Any]) -> str | None:
    directory = index_data.get("directory")
    items = directory.get("item", []) if isinstance(directory, Mapping) else []
    if isinstance(items, Mapping):
        items = [items]
    candidates: list[tuple[int, str]] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("name") or "")
        lower = name.lower()
        if not lower.endswith((".htm", ".html")):
            continue
        if lower.startswith("ex") or re.match(r"r\d+\.(?:htm|html)$", lower):
            continue
        try:
            size = int(item.get("size") or 0)
        except (TypeError, ValueError):
            size = 0
        candidates.append((size, name))
    if candidates:
        return max(candidates, key=lambda candidate: (candidate[0], candidate[1]))[1]

    metadata = index_data.get("filingMetadata")
    if isinstance(metadata, Mapping):
        primary = metadata.get("primaryDocument")
        if primary:
            return str(primary)
    return None


class SECFilingFetcher:
    """Small SEC-only fetch/cache layer used by the site build."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last_request_at = 0.0
        self._filing_cache: dict[str, dict[str, Any]] = {}

    def _download(self, url: str) -> str:
        _safe_host(url)
        cache_path = self.cache_dir / _cache_name(url)
        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8")

        wait = REQUEST_INTERVAL_SECONDS - (time.monotonic() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)
        request = Request(
            url,
            headers={
                "User-Agent": SEC_USER_AGENT,
                "Accept-Encoding": "identity",
            },
        )
        with urlopen(request, timeout=30) as response:
            data = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
        self._last_request_at = time.monotonic()
        text = data.decode(charset, errors="replace")
        cache_path.write_text(text, encoding="utf-8")
        return text

    def load_filing(self, evidence: Mapping[str, Any]) -> dict[str, Any]:
        """Fetch/cache a filing index and its primary inline document."""

        cache_key = str(evidence.get("filing_url") or evidence.get("accn") or "")
        if cache_key in self._filing_cache:
            return self._filing_cache[cache_key]
        folder_url = _filing_folder_url(evidence)
        if not folder_url:
            raise ValueError("evidence has no SEC filing URL")

        index_url = f"{folder_url}/index.json"
        index_data = json.loads(self._download(index_url))
        primary = _select_primary_document(index_data)
        if not primary:
            raise ValueError("SEC index.json did not identify a primary HTML document")
        primary_url = f"{folder_url}/{primary}"
        html = self._download(primary_url)

        _, cik, accn_nodash = _accession_parts(evidence)
        if not cik or not accn_nodash:
            parts = [part for part in urlparse(folder_url).path.split("/") if part]
            if "data" in parts:
                data_index = parts.index("data")
                cik = cik or (parts[data_index + 1] if len(parts) > data_index + 1 else None)
                accn_nodash = accn_nodash or (parts[data_index + 2] if len(parts) > data_index + 2 else None)
        inline_url = None
        if cik and accn_nodash:
            inline_url = f"https://www.sec.gov/ix?doc=/Archives/edgar/data/{cik}/{accn_nodash}/{primary}"

        filing = {
            "html": html,
            "index": index_data,
            "primary_document": primary,
            "primary_url": primary_url,
            "inline_url": inline_url,
        }
        self._filing_cache[cache_key] = filing
        return filing


def _missing_accession_reason(evidence: Mapping[str, Any]) -> str | None:
    _, _, accn_nodash = _accession_parts(evidence)
    if not accn_nodash:
        return "evidence has no accession number; no filing passage can be located"
    if not evidence.get("filing_url"):
        return "evidence has an accession but no SEC filing URL"
    return None


def excerpt_for_evidence(evidence: Mapping[str, Any], fetcher: SECFilingFetcher) -> dict[str, Any]:
    """Return one excerpt record, including an explicit null reason on failure."""

    result: dict[str, Any] = {
        "evidence_id": evidence.get("id"),
        "excerpt": None,
        "reason": None,
        "primary_url": None,
        "inline_url": None,
        "primary_document": None,
    }
    missing_reason = _missing_accession_reason(evidence)
    if missing_reason:
        result["reason"] = missing_reason
        return result

    try:
        filing = fetcher.load_filing(evidence)
    except Exception as error:  # A single filing must not prevent the site build.
        result["reason"] = f"SEC filing download failed: {error}"
        return result

    result["primary_url"] = filing["primary_url"]
    result["inline_url"] = filing["inline_url"]
    result["primary_document"] = filing["primary_document"]
    parsed = extract_filing_excerpt(filing["html"], evidence)
    result["excerpt"] = parsed.get("excerpt")
    result["reason"] = parsed.get("reason")
    return result


def excerpt_fact_key(
    evidence: Mapping[str, Any], record: Mapping[str, Any], evidence_index: int
) -> tuple[Any, ...]:
    """Return the stable identity used to merge duplicate evidence blocks."""

    excerpt = record.get("excerpt")
    if not excerpt:
        return ("unmatched", evidence_index)
    fact = excerpt.get("fact") or {}
    full_value = fact.get("full_value")
    if full_value is None:
        full_value = evidence.get("value")
    return (
        evidence.get("accn"),
        evidence.get("concept"),
        evidence.get("start"),
        evidence.get("end"),
        evidence.get("unit"),
        full_value,
    )


def group_excerpt_records(
    evidence_rows: Iterable[Mapping[str, Any]], records: Iterable[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Group records that point to the same filing fact, preserving row identity."""

    evidence_list = list(evidence_rows)
    record_list = list(records)
    records_by_index = {
        int(record.get("evidence_index")): record
        for record in record_list
        if isinstance(record.get("evidence_index"), int)
    }
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    role_rank = {"current": 0, "comparison": 1}
    for evidence_index, evidence in enumerate(evidence_list):
        record = records_by_index.get(evidence_index)
        if record is None:
            record = {
                "evidence_index": evidence_index,
                "evidence_key": f"{evidence.get('id') or 'evidence'}:{evidence_index}",
            }
        key = excerpt_fact_key(evidence, record, evidence_index)
        group = groups.setdefault(
            key,
            {
                "fact_key": list(key),
                "evidence_indices": [],
                "evidence_keys": [],
            },
        )
        group["evidence_indices"].append(evidence_index)
        group["evidence_keys"].append(record.get("evidence_key"))

    result = list(groups.values())
    for group in result:
        group["evidence_indices"].sort(
            key=lambda index: (
                role_rank.get(evidence_list[index].get("role"), 0),
                index,
            )
        )
        ordered_keys = []
        for index in group["evidence_indices"]:
            record = records_by_index.get(index)
            ordered_keys.append(record.get("evidence_key") if record else f"evidence:{index}")
        group["evidence_keys"] = ordered_keys
    result.sort(key=lambda group: group["evidence_indices"][0])
    return result


def claim_excerpts(claim: Mapping[str, Any], fetcher: SECFilingFetcher) -> list[dict[str, Any]]:
    """Extract one record for every evidence component on a verified claim."""

    if claim.get("status") != "verified":
        return []
    records = []
    for evidence_index, evidence in enumerate(claim.get("evidence") or []):
        record = excerpt_for_evidence(evidence, fetcher)
        evidence_id = evidence.get("id")
        role = evidence.get("role")
        record["evidence_index"] = evidence_index
        record["evidence_key"] = (
            f"{evidence_id}:{role}" if evidence_id and role else f"{evidence_id}:{evidence_index}"
        )
        record["evidence_id"] = evidence_id
        record["role"] = role
        records.append(record)
    return records


__all__ = [
    "SEC_USER_AGENT",
    "SECFilingFetcher",
    "claim_excerpts",
    "excerpt_fact_key",
    "excerpt_for_evidence",
    "extract_filing_excerpt",
    "group_excerpt_records",
    "parse_contexts",
    "parse_inline_xbrl",
]
