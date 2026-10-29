"""Independent, annotation-driven L4 gold builder. No claimcheck imports/models.

Financial references are transcribed against SEC source bytes using explicit
table/column coordinates or a literal sentence regex. Decimal comparisons and
claim rendering here do not call the runtime parser or verdict program.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIXTURES = ROOT / "tests/fixtures/releases"
FACTORS = {"": Decimal(1), "million": Decimal(1000000), "billion": Decimal(1000000000)}


class ReferenceHTML(HTMLParser):
    """A separate coordinate reader; deliberately no semantic inference."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.tables = {}
        self.stack = []
        self.cell = None
        self.row = None
        self.column = 0
        self.count = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.count += 1
            self.stack.append(self.count)
            self.tables[self.count] = []
        if tag == "tr":
            self.row, self.column = [], 0
        if tag in {"td", "th"} and self.row is not None:
            self.cell = {"column": self.column, "width": int(dict(attrs).get("colspan", 1)), "parts": []}
        if tag == "br":
            self.text.append(" ")
            if self.cell is not None:
                self.cell["parts"].append(" ")

    def handle_data(self, data):
        self.text.append(data)
        if self.cell is not None:
            self.cell["parts"].append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.cell["text"] = re.sub(r"\s+", " ", "".join(self.cell.pop("parts"))).strip()
            self.column += self.cell["width"]
            self.row.append(self.cell)
            self.cell = None
        if tag == "tr" and self.row is not None and self.stack:
            self.tables[self.stack[-1]].append(self.row)
            self.row = None
        if tag == "table" and self.stack:
            self.stack.pop()
        if tag in {"p", "div", "tr", "td", "h1", "h2", "h3"}:
            self.text.append(" ")


def reference_value(source, annotation):
    path = FIXTURES / "releases" / hashlib.sha256(source["exhibit_url"].encode()).hexdigest()
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source["sha256"]
    parser = ReferenceHTML()
    parser.feed(raw.decode())
    text = re.sub(r"\s+", " ", "".join(parser.text))
    reference = annotation["reference"]
    if reference.get("context_anchor"):
        assert reference["context_anchor"] in text
    if "insufficient" in reference:
        if reference["insufficient"] == "no_outlook":
            assert not re.search(r"\b(?:outlook|guidance)\b", text, re.I)
        elif reference["insufficient"] == "absent_metric":
            assert not re.search(reference["absent_pattern"], text, re.I)
        elif reference["insufficient"] == "ttm_only":
            assert re.search(r"Free cash flow.{0,40}(?:TTM|trailing twelve months)", text, re.I)
        return None, {"note": reference["insufficient"], "source_sha256": source["sha256"]}
    factor = FACTORS[reference["scale"]]
    if "table" in reference:
        rows = parser.tables[reference["table"]]
        matches = [(i, r) for i, r in enumerate(rows) if r and r[0]["text"] == reference["label"]]
        matches = [(i, r) for i, r in matches if any(c["column"] == reference["column"] and re.search(r"\d", c["text"]) for c in r)]
        assert len(matches) == 1, (annotation["id"], "ambiguous manual reference")
        index, row = matches[0]
        headers = " ".join(c["text"] for r in rows[:index] for c in r)
        for header in reference["headers"]:
            assert header in headers, (annotation["id"], header)
        cell = next(c["text"] for c in row if c["column"] == reference["column"])
        pieces = re.findall(r"\(?-?\d[\d,]*(?:\.\d+)?\)?", cell)
        values = [(-Decimal(p[1:-1].replace(",", "")) if p.startswith("(") else Decimal(p.replace(",", ""))) * factor for p in pieces]
        assert len(values) in {1, 2}
        low, high = values[0], values[-1]
        audit = {"table": reference["table"], "row_label": reference["label"], "column": reference["column"], "cell": cell, "headers": reference["headers"]}
        if reference.get("context_anchor"):
            audit["context_anchor"] = reference["context_anchor"]
    else:
        matches = list(re.finditer(reference["pattern"], text))
        assert len(matches) == 1, (annotation["id"], "sentence anchor")
        match = matches[0]
        a, b = Decimal(match[1]), Decimal(match[2])
        if reference.get("plus_minus") == "percent":
            low, high = a * factor * (1 - b / 100), a * factor * (1 + b / 100)
        elif reference.get("plus_minus") == "million":
            low, high = a * factor - b * FACTORS["million"], a * factor + b * FACTORS["million"]
        else:
            low, high = a * factor, b * factor
        audit = {"quote": match[0], "period_anchor": reference["period_anchor"]}
        assert reference["period_anchor"] in text
    audit.update(low=str(low), high=str(high), source_sha256=source["sha256"])
    return (low, high), audit


def build():
    sources = {s["ticker"]: s for s in json.loads((FIXTURES / "manifest.json").read_text())}
    annotations = json.loads((HERE / "annotations.json").read_text())
    assert len(annotations) == 32 and len({a["ticker"] for a in annotations}) == 8
    claims, facts = [], {}
    for a in annotations:
        source = sources[a["ticker"]]
        actual, audit = reference_value(source, a)
        factor = FACTORS[a["claim_scale"]]
        claimed = tuple(Decimal(n) * factor for n in a["claim_values"])
        asserted = claimed if len(claimed) == 2 else (claimed[0], claimed[0])
        verdict = "insufficient_evidence" if actual is None else "supported" if asserted == actual else "contradicted"
        amounts = [f"${n}" + (f" {a['claim_scale']}" if a["claim_scale"] else "") for n in a["claim_values"]]
        value_text = " to ".join(amounts)
        claim = f"{a['ticker']} {'expects' if a['kind'] == 'guidance' else 'reported'} {a['label']} of {value_text} for {a['period']}."
        if a.get("claim_override"):
            claim = a["claim_override"]
        claims.append({"id": a["id"], "ticker": a["ticker"], "claim": claim, "kind": a["kind"],
                       "metric": a["metric"], "period": a["period"], "gold_verdict": verdict,
                       "source_tier": "generated", "source_url": source["exhibit_url"],
                       "accession": source["accession"], "source_sha256": source["sha256"],
                       "gold_note": a["note"]})
        facts[a["id"]] = audit
    (HERE / "claims.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in claims))
    (HERE / "gold_facts.json").write_text(json.dumps(facts, indent=2) + "\n")
    manifest = {"claims": len(claims), "companies": sorted(sources), "counts": dict(Counter(c["gold_verdict"] for c in claims)),
                "model_calls": 0, "runtime_parser_imported": False,
                "files": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in ("annotations.json", "claims.jsonl", "gold_facts.json", "build_gold.py")}}
    (HERE / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "files"}))
    return claims


if __name__ == "__main__":
    build()
