"""L4 earnings-release candidates: issuer/label/period/number bindings in code."""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from typing import Any

from .release_fetch import ReleaseClient, ReleaseError
from .release_text import Document, SCALE, date_labels, number, parse_html, period_labels


RELEASE_KINDS = ("guidance", "non_gaap", "reported_in_release")
METRIC_PATTERNS = {
    "adjusted_eps": r"(?:non[ -]gaap|adjusted)\s+(?:(?:basic\s+and\s+)?diluted\s+)?(?:eps|(?:net\s+income|earnings)\s+per\s+(?:diluted\s+)?share)",
    "adjusted_operating_income": r"(?:non[ -]gaap|adjusted)\s+(?:operating\s+(?:income|profit)(?:\s*\(loss\))?|income\s+from\s+operations)",
    "adjusted_free_cash_flow": r"adjusted\s+free\s+cash\s+flow",
    "free_cash_flow": r"(?<!adjusted )\bfree\s+cash\s+flow\b",
    "revenue": r"\b(?:(?:total|gaap)\s+)?(?:revenue[s]?|(?:total\s+)?net\s+sales)\b",
    "operating_income": r"\boperating\s+(?:income|profit)\b",
    "net_income": r"\bnet\s+income\b",
    "eps_diluted": r"\b(?:diluted\s+(?:eps|(?:net\s+income|earnings)\s+per\s+share)|(?:earnings|net\s+income)\s+per\s+diluted\s+share|eps)\b",
}
METRICS = tuple(METRIC_PATTERNS)
_OUTLOOK = re.compile(r"\b(?:outlook|guidance|expects?|expected|forecast(?:ing)?|targets|targeting|guides?)\b|\b(?:revenue|earnings|eps|financial)\s+target\b", re.I)
_NON_GAAP = re.compile(r"\b(?:non[ -]gaap|adjusted)\b", re.I)


def requires_release(text: str) -> bool:
    """A model cannot relabel guidance/non-GAAP as a generic XBRL value."""
    return bool(_OUTLOOK.search(text) or _NON_GAAP.search(text) or re.search(r"\bfree cash flow\b", text, re.I))


def metric_match(text: str, metric: str) -> re.Match[str] | None:
    return re.search(METRIC_PATTERNS[metric], text, re.I)


def infer_metric(text: str) -> str | None:
    for metric in METRICS:
        if metric_match(text, metric):
            return metric
    return None


def _short_years(text: str) -> str:
    return re.sub(r"\bFY\s*['’]?(\d{2})\b", lambda m: "FY20" + m[1], text, flags=re.I)


def claim_periods(text: str) -> set[str]:
    periods = set(re.findall(r"\b(?:FY20\d{2}(?:Q[1-4])?|20\d{2}Q[1-4])\b", text.upper()))
    periods.update(period_labels(text))
    if re.search(r"\bcalendar\b", text, re.I):
        periods = {p.removeprefix("FY") if "Q" in p else p for p in periods}
    return periods


def claim_number(text: str, metric: str) -> dict[str, Any] | None:
    """Read the user's numeric assertion after its label, never a model value."""
    match = metric_match(text, metric)
    if not match:
        return None
    tail = text[match.end():]
    tail = re.sub(r"\b(?:FY\s*)?20\d{2}(?:Q[1-4])?\b|\bQ[1-4]\b", "", tail, flags=re.I)
    # Named fiscal/calendar periods between metric and value contain ordinal
    # words, not financial numbers. Remove month-date phrases as well.
    tail = re.sub(r"\b(?:Jan\w*|Feb\w*|Mar\w*|Apr\w*|May|Jun\w*|Jul\w*|Aug\w*|Sep\w*|Oct\w*|Nov\w*|Dec\w*)\.?\s+\d{1,2},?", "", tail, flags=re.I)
    return number(tail, per_share=metric in {"adjusted_eps", "eps_diluted"})


def _scope(doc: Document) -> tuple[str | None, str | None]:
    report = None
    for span in doc.spans[:60]:
        text = _short_years(span["text"])
        labels = period_labels(text)
        if len(labels) == 1 and not _OUTLOOK.search(text):
            report = next(iter(labels))
            break
        if re.search(r"quarter\s+ended", text, re.I) and (dates := date_labels(text)):
            q = re.search(r"(first|second|third|fourth)[ -]+quarter\s+ended", text, re.I)
            if q:
                report = f"FY{dates[-1][:4]}Q{['first', 'second', 'third', 'fourth'].index(q[1].lower()) + 1}"
                break
    end = None
    for span in doc.spans[:80]:
        if re.search(r"quarter.{0,40}ended", span["text"], re.I):
            # Filing/press-release date can precede period end in the same
            # sentence; take the date after 'ended'.
            tail = re.split(r"\bended\b", span["text"], maxsplit=1, flags=re.I)[-1]
            dates = date_labels(tail)
            if dates:
                end = dates[0]
                break
    if end is None:
        # First complete date header under a quarterly table is explicitly
        # bound to the release's reporting quarter (not the publication date).
        for i, span in enumerate(doc.spans):
            if span["kind"] != "table_row":
                continue
            prev = " ".join(s["text"] for s in doc.spans[max(0, i - 4):i + 1])
            if re.search(r"three\s+months\s+ended", prev, re.I) and (dates := date_labels(span["text"])):
                end = dates[0]
                break
    return report, end


def _overlap(header: dict[str, Any], cell: dict[str, Any]) -> bool:
    return header["column"] <= cell["column"] < header["column"] + header["colspan"]


def _column_context(rows: list[dict[str, Any]], cell: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    headers = []
    for row in rows:
        nonempty = [c for c in row.get("cells", []) if c["text"]]
        if not nonempty:
            continue
        first = nonempty[0]
        if first["column"] == 0 and not re.match(r"^(?:\(?in\s+(?:millions|thousands)|\(?\$\s+in|three months|six months|nine months|year ended|fiscal\s|fy\s*\d|q[1-4]\b)", first["text"], re.I):
            continue
        for header in row.get("cells", []):
            text = header["text"]
            if _overlap(header, cell) and (re.search(r"months? ended|year ended|\bq[1-4]\b|\bfiscal\b|\bfy\s*\d|(?:19|20)\d{2}$", text, re.I)
                    or date_labels(text + " 2000")):
                # Metric value cells such as 2,025 are not year headers.
                if len(text) < 100 and not re.search(r"\$|%|,\d{3}", text):
                    headers.append(header)
    return " ".join(h["text"] for h in headers), headers


def _column_period(context: str, report: str | None, report_end: str | None) -> tuple[set[str], str]:
    text = _short_years(context)
    if re.search(r"\b(?:six|nine)\s+months\s+ended", text, re.I):
        return set(), "ytd"
    if re.search(r"trailing|\bttm\b|twelve months", text, re.I):
        return set(), "ttm"
    labels = period_labels(text)
    if labels:
        return labels, "quarter" if any("Q" in p for p in labels) else "annual"
    dates = date_labels(text)
    if report and report_end and dates and re.search(r"three months ended", text, re.I):
        end = dates[-1]
        if end == report_end:
            return {report}, "quarter"
        # Comparative prior-year columns are explicit dates, not a second
        # current-quarter number. Do not infer arbitrary prior fiscal quarters.
        if end[:4] == str(int(report_end[:4]) - 1) and end[5:7] == report_end[5:7]:
            return {re.sub(r"20\d{2}", lambda m: str(int(m[0]) - 1), report)}, "quarter"
    return set(), "unknown"


def _period_matches(requested: str, labels: set[str], calendar: bool) -> bool:
    if requested in labels:
        return True
    return calendar and not requested.startswith("FY") and "FY" + requested in labels


def _numeric_cell(text: str) -> bool:
    text = text.replace("−", "-")
    return bool(re.fullmatch(r"\(?\$?\s*[+-]?\d[\d,.]*\)?(?:\s*(?:billion|million|thousand))?(?:\s*(?:-|–|to)\s*\$?\d[\d,.]*(?:\s*(?:billion|million|thousand))?)?", text, re.I))


def extract_candidates(doc: Document, metric: str, kind: str, period: str, *, calendar: bool = False) -> list[dict[str, Any]]:
    report, report_end = _scope(doc)
    found: list[dict[str, Any]] = []
    by_table: dict[int, list[dict[str, Any]]] = {}
    table_prefix: dict[int, str] = {}
    outlook_heading: dict[str, Any] | None = None
    for i, span in enumerate(doc.spans):
        text = span["text"]
        labels = period_labels(_short_years(text), context=report)
        if span["kind"] == "text" and labels and _OUTLOOK.search(text) and len(text) < 350 and "$" not in text:
            outlook_heading = span
        if span["kind"] == "text" and (re.search(r"financial (?:statements|highlights)|consolidated|about (?:nvidia|adobe|amd|intel|amazon|salesforce)", text, re.I)
                                           or "forward-looking" in text.lower()):
            outlook_heading = None
        if span["kind"] != "table_row":
            if kind != "guidance" or not metric_match(text, metric) or not _OUTLOOK.search(text):
                continue
            for sentence in re.finditer(r".+?(?:[.!?](?=\s+[A-Z]|$)|$)", text):
                value_text = sentence[0].strip()
                # Parallel GAAP/non-GAAP points are not one financial range.
                # Without explicit cell bindings, 'respectively' is ambiguous.
                if re.search(r"\brespectively\b|\bGAAP\s+and\s+non[ -]GAAP\b", value_text, re.I):
                    continue
                m = metric_match(value_text, metric)
                if not m or not _OUTLOOK.search(value_text):
                    continue
                if re.search(r"not (?:providing|provide)|not assumed|not include", value_text, re.I):
                    continue
                prefix = value_text[:m.start()]
                context = prefix if period_labels(prefix, context=report) else (outlook_heading or {}).get("text", "")
                target = period_labels(context, context=report)
                if not _period_matches(period, target, calendar):
                    continue
                tail = value_text[m.end():]
                money = re.search(r"\$\s*\(?[+-]?\d", tail)
                if not money or money.start() > 80 or re.search(r"\d", tail[:money.start()]):
                    continue
                # 'total revenue to be in the range of ...' begins with value.
                parsed = number(tail, per_share=metric in {"adjusted_eps", "eps_diluted"})
                if parsed is None:
                    continue
                # Reject a second metric before the first financial number.
                if any(metric_match(tail[:parsed["number_start"]], other) for other in METRICS if other != metric):
                    continue
                start = span["start"] + sentence.start() + len(sentence[0]) - len(sentence[0].lstrip())
                end = start + len(value_text)
                hstart = start + m.end() + parsed["number_start"]
                found.append({"start": start, "end": end, "quote": doc.text[start:end],
                              "highlight_offsets": [[hstart, start + m.end() + parsed["number_end"]]],
                              "period": period, "period_type": "quarter" if "Q" in period else "annual",
                              "label": m[0], "context_spans": [outlook_heading] if outlook_heading else [], **parsed})
            continue

        rows = by_table.setdefault(span["table"], [])
        if not rows:
            table_prefix[span["table"]] = doc.text[max(0, span["start"] - 800):span["start"]]
        previous = list(rows)
        rows.append(span)
        cells = [c for c in span.get("cells", []) if c["text"]]
        if not cells:
            continue
        label = cells[0]["text"]
        if len(label) > 140 or not metric_match(label, metric):
            continue
        # Entire-company totals only. A familiar word in a segment, margin,
        # growth or share-count label is not the requested financial measure.
        if re.search(r"segment|margin|growth|change|shares used|excluding|effect|impact|adjustments|\bttm\b|trailing", label, re.I):
            continue
        if metric in {"revenue", "operating_income", "net_income", "eps_diluted"} and _NON_GAAP.search(label):
            continue
        if metric == "free_cash_flow" and re.search(r"adjusted", label, re.I):
            continue
        if metric == "revenue" and not re.fullmatch(r"(?:(?:gaap|total)\s+)?(?:revenues?|(?:total\s+)?net\s+sales)(?:\s*\(\d+\))?", label, re.I):
            continue
        if metric == "revenue" and re.fullmatch(r"net sales", label, re.I):
            sections = [r["text"] for r in previous if re.search(r"north america|international|\baws\b|consolidated", r["text"], re.I)]
            if sections and "consolidated" not in sections[-1].lower():
                continue
        if metric in {"adjusted_eps", "eps_diluted"} and not re.search(r"\bdiluted\b", label, re.I):
            continue
        for cell in cells[1:]:
            if not _numeric_cell(cell["text"]):
                continue
            col_context, headers = _column_context(previous, cell)
            target, period_type = _column_period(col_context, report, report_end)
            guidance_context = outlook_heading and period_labels(outlook_heading["text"], context=report)
            is_future = bool(target and report and any(p > report for p in target))
            is_guidance = bool(is_future or (guidance_context and (not target or target.intersection(guidance_context))))
            if kind == "guidance":
                if not is_guidance:
                    continue
                if not target:
                    target = guidance_context or set()
                    period_type = "quarter" if any("Q" in p for p in target) else "annual"
            elif is_guidance:
                continue
            if not _period_matches(period, target, calendar):
                continue
            nearby = " ".join(s["text"] for s in doc.spans[max(0, i - 7):i] if s["table"] in {None, span["table"]})
            table_text = " ".join(s["text"] for s in previous[:15]) + " " + nearby + " " + table_prefix[span["table"]]
            scale_match = re.search(r"\bin\s+(thousands|millions|billions)\b", table_text, re.I)
            per_share = metric in {"adjusted_eps", "eps_diluted"}
            if not per_share and not scale_match and not re.search(r"million|billion|thousand", cell["text"], re.I):
                continue
            scale = SCALE.get(scale_match[1].lower().rstrip("s"), Decimal(1)) if scale_match else Decimal(1)
            parsed = number(cell["text"], scale=scale, per_share=per_share)
            if parsed is None:
                continue
            start, end = cells[0]["start"], cell["end"]
            if end - start > 450:
                continue
            found.append({"start": start, "end": end, "quote": doc.text[start:end],
                          "highlight_offsets": [[cell["start"] + parsed["number_start"], cell["start"] + parsed["number_end"]]],
                          "period": period, "period_type": period_type, "label": label,
                          "period_end": (date_labels(col_context) or [report_end])[-1],
                          "context_spans": headers + ([outlook_heading] if kind == "guidance" and outlook_heading else []), **parsed})
    return found


def provenance(source: dict[str, Any]) -> dict[str, Any]:
    return {"tier": "L4", "audited": False, "furnished": True, "unaudited": True,
            "confirmations": 1, "forms": [source["form"]], "first_filed": source["filed"],
            "latest_filed": source["filed"], "restated": False, "amended": False,
            "strength": "medium"}


class ReleaseService:
    def __init__(self, edgar: Any, client: ReleaseClient | None = None) -> None:
        self.edgar = edgar
        self.client = client or ReleaseClient(edgar.cache_dir, user_agent=edgar.user_agent, timeout=edgar.timeout)
        self.candidates: dict[str, dict[str, Any]] = {}

    def find(self, ticker: str, metric: str, period: str, claim_kind: str) -> dict[str, Any]:
        if metric not in METRICS or claim_kind not in RELEASE_KINDS:
            raise ReleaseError("unsupported release metric or claim kind")
        company = self.edgar.resolve_ticker(ticker)
        if "error" in company:
            return company
        calendar = self.edgar.fiscal_equals_calendar(ticker) is True
        inspected, candidates, failures = [], [], []
        filings = self.client.filings(company["cik"], period)
        # Bound network work, not the interpretation of the requested period.
        # A valid same-period number must still be present in the exhibit text.
        for filing in filings[:32]:
            try:
                exhibits = self.client.exhibits(company["cik"], filing)
            except Exception as exc:
                failures.append({"accession": filing["accessionNumber"], "error": type(exc).__name__})
                continue
            for exhibit in exhibits:
                source = {k: v for k, v in exhibit.items() if k != "raw"}
                inspected.append(source)
                doc = parse_html(exhibit["raw"])
                for candidate in extract_candidates(doc, metric, claim_kind, period, calendar=calendar):
                    identity = f"{source['sha256']}:{candidate['start']}:{candidate['end']}:{metric}:{claim_kind}:{period}"
                    cid = hashlib.sha256(identity.encode()).hexdigest()[:24]
                    value = {**source, **candidate, "ticker": company["ticker"], "entity": company["entity"],
                             "metric": metric, "claim_kind": claim_kind, "candidate_id": cid,
                             "value": candidate["low"] if candidate["low"] == candidate["high"] else None,
                             "calendar_equals_fiscal": calendar, "provenance": provenance(source)}
                    self.candidates[cid] = value
                    candidates.append(value)
            # All same-period revisions must be considered; never silently
            # pick one value just because it was returned first.
        return {"ticker": company["ticker"], "metric": metric, "period": period,
                "claim_kind": claim_kind, "candidates": candidates[:24], "inspected": inspected,
                "failures": failures, "search_truncated": len(filings) > 32,
                "error": None if candidates else "insufficient_evidence"}

    def quote(self, candidate_id: str, start: int, end: int) -> dict[str, Any]:
        stored = self.candidates.get(candidate_id)
        if stored is None or (start, end) != (stored["start"], stored["end"]):
            raise ReleaseError("unknown candidate or offsets do not match a returned span")
        raw, meta = self.client.read(stored["exhibit_url"])
        if meta["sha256"] != stored["sha256"]:
            raise ReleaseError("release snapshot changed")
        doc = parse_html(raw)
        # Re-extract from bytes: neither a model-chosen number nor a mutable
        # tool response is an authority for the numeric result.
        valid = [c for c in extract_candidates(doc, stored["metric"], stored["claim_kind"], stored["period"],
                                              calendar=stored["calendar_equals_fiscal"])
                 if c["start"] == start and c["end"] == end and doc.text[start:end] == stored["quote"]]
        if len(valid) != 1:
            raise ReleaseError("span failed deterministic re-extraction")
        value = {**stored, **valid[0], "span_verified": True}
        value["value"] = value["low"] if value["low"] == value["high"] else None
        from .evidence import SecReleaseConnector
        value["evidence_record"] = SecReleaseConnector().export(
            quote=value, raw=raw, text=doc.text, metadata=meta).to_dict()
        return value
