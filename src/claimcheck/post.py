"""Check a pasted social post or article: extract its financial claims, then verify each one.

The model only proposes claims. The program keeps a claim for verification only when its quote is an exact span of
the post and every number in the rewritten claim also appears in that quote, so a model cannot invent or alter what
the post said. Issuer guidance can be checked against L4 releases; opinions and
third-party forecasts remain outside filing verification.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from .agent import verify_claim
from .budget import Ledger
from .checks import program_check_gap
from .edgar import EdgarClient
from .providers import get_provider
from .trace import TraceRecorder, write_trace
from .release_report import render_release_quote

EXTRACTION_PROMPT = """You extract financial claims from a social media post or article so they can be checked against SEC filings.

Return only JSON, with no prose and no code fence, in this shape:
{"claims": [{"quote": "...", "claim": "...", "ticker": "...", "kind": "..."}]}

Rules for each item:
- quote: the exact span of the post that states the claim, copied character for character (same language, same punctuation). Keep it short: one sentence or clause.
- claim: one standalone English sentence that names the company and keeps every number, unit, period and direction word from the quote. Convert East Asian units to standard English scale words: 億 = hundred million, so 2,451 億美元 = $245.1 billion and 623 億 = $62.3 billion; 萬 = ten thousand. Write currency as $ only when the post says US dollars (美元); otherwise keep the currency it names. Do not add a period, number or company that the post does not state. If the post says "last quarter" without a date, keep "last quarter".
- ticker: the US stock ticker if the company is clear, otherwise null.
- kind: "reported_fact" for results a company reported, including non-GAAP measures; "issuer_guidance" for a claim about the company's own stated guidance, expectations or financial targets; "forecast" for analysts' or other third parties' predictions; "opinion" for valuations, recommendations or judgments; "other" for anything else with a number (stock price moves, market share, user counts).
Include every sentence that contains a number about a company. Return {"claims": []} if there are none.

Post:
"""

MAX_POST_CHARS = 6000
MAX_EXTRACTION_TOKENS = 4000
KINDS = {"reported_fact", "issuer_guidance", "forecast", "opinion", "other"}
_DIGITS = re.compile(r"\d[\d,]*(?:\.\d+)?")


class PostError(RuntimeError):
    pass


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def locate_quote(post: str, quote: str) -> tuple[int, int] | None:
    """Character offsets of ``quote`` in ``post``, tolerating whitespace differences only."""

    if not quote:
        return None
    start = post.find(quote)
    if start >= 0:
        return start, start + len(quote)
    words = [re.escape(word) for word in _normalize_space(quote).split(" ")]
    match = re.search(r"\s+".join(words), post)
    return (match.start(), match.end()) if match else None


_CJK_SCALE = re.compile(r"(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>hundred million|ten thousand)", re.IGNORECASE)


def normalize_scale_words(claim: str) -> str:
    """Rewrite literal translations of 億/萬 ("2,451 hundred million") as billions/thousands ("245.1 billion").

    The verifier's number parser reads "hundred million" as million, which turned a false "over 500 億" claim true.
    """

    def repl(match: re.Match[str]) -> str:
        value = float(match.group("num").replace(",", ""))
        if match.group("unit").lower() == "hundred million":
            return f"{value / 10:g} billion"
        return f"{value * 10:g} thousand"

    return _CJK_SCALE.sub(repl, claim)


def _digit_key(raw: str) -> str:
    """Significant digits of a number phrase: "$143.1" and "1,431" both give "1431"."""

    digits = raw.replace(",", "").replace(".", "").lstrip("0")
    return digits.rstrip("0") or "0"


def numbers_in(text: str) -> list[str]:
    return [match.group(0) for match in _DIGITS.finditer(text)]


def numbers_preserved(claim: str, quote: str, context: str = "") -> tuple[bool, list[str]]:
    """Every number in the rewritten claim must appear in the quote (ignoring unit scaling such as 億 vs billion).

    Years and quarter digits may come from elsewhere in the post (a headline often states the period once), but
    they must appear somewhere in it, so a claim cannot add a period the post never stated.
    """

    quote_keys = {_digit_key(raw) for raw in numbers_in(quote)}
    context_keys = {_digit_key(raw) for raw in numbers_in(context)}
    missing = []
    for raw in numbers_in(claim):
        key = _digit_key(raw)
        if key in quote_keys:
            continue
        period_like = re.fullmatch(r"(19|20)\d\d|[1-4]", raw) is not None
        if period_like and key in context_keys:
            continue
        missing.append(raw)
    return not missing, missing


def _strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text


def parse_extraction(raw_text: str) -> list[dict[str, Any]]:
    text = _strip_fence(raw_text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise PostError("extraction response was not JSON")
        value = json.loads(text[start : end + 1])
    claims = value.get("claims") if isinstance(value, Mapping) else None
    if not isinstance(claims, list):
        raise PostError("extraction response has no claims list")
    return [item for item in claims if isinstance(item, Mapping)]


def screen_claims(post: str, proposed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Apply the program's acceptance rules to model-proposed claims."""

    screened: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in proposed:
        quote = str(item.get("quote") or "").strip()
        claim = normalize_scale_words(_normalize_space(str(item.get("claim") or "")))
        kind = str(item.get("kind") or "other")
        kind = kind if kind in KINDS else "other"
        ticker = item.get("ticker")
        key = claim.casefold()
        if not claim or key in seen:
            continue
        seen.add(key)
        span = locate_quote(post, quote)
        preserved, missing = numbers_preserved(claim, quote, post)
        if span is None:
            status, reason = "rejected", "quote is not an exact span of the post"
        elif not numbers_in(quote):
            status, reason = "rejected", "quote has no number"
        elif not preserved:
            status, reason = "rejected", "claim has numbers the quote does not: " + ", ".join(missing)
        elif kind not in {"reported_fact", "issuer_guidance"}:
            status, reason = "not_checked", {
                "forecast": "third-party forecast; not the issuer's own stated guidance",
                "opinion": "opinion or valuation; not a reported fact",
                "other": "not a reported financial result in SEC filings (for example a stock price or user count)",
            }[kind]
        else:
            status, reason = "to_verify", ""
        screened.append(
            {
                "index": len(screened) + 1,
                "quote": quote,
                "span": list(span) if span else None,
                "claim": claim,
                "ticker": ticker if isinstance(ticker, str) and ticker else None,
                "kind": kind,
                "status": status,
                "screen_reason": reason,
            }
        )
    return screened


def _extraction_payload(adapter: Any, post: str, model: str) -> dict[str, Any]:
    if adapter.chat_completions:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": post},
            ],
            "max_tokens": MAX_EXTRACTION_TOKENS,
        }
    return {
        "model": model,
        "instructions": EXTRACTION_PROMPT,
        "input": [{"role": "user", "content": post}],
        "max_output_tokens": MAX_EXTRACTION_TOKENS,
    }


def extract_claims(
    post: str,
    *,
    client: Any,
    ledger: Ledger,
    model: str,
    provider: str,
    recorder: TraceRecorder,
) -> list[dict[str, Any]]:
    adapter = get_provider(provider)
    request = _extraction_payload(adapter, post, model)
    reservation = ledger.reserve(request, model=model, max_output_tokens=MAX_EXTRACTION_TOKENS, provider=provider)
    started = time.perf_counter()
    response = adapter.call(client, request)
    latency_ms = (time.perf_counter() - started) * 1000
    cost = ledger.reconcile(reservation, response.usage)
    recorder.record_request(
        payload=request,
        response=response.raw_response,
        reservation=reservation,
        usage=response.normalized_usage if adapter.chat_completions else response.usage,
        cost=cost,
        latency_ms=latency_ms,
        status=response.status,
        finish_reason=getattr(response, "finish_reason", None),
    )
    if response.status != "completed":
        raise PostError(f"extraction response status was {response.status}")
    return parse_extraction(str(getattr(response, "text", "") or ""))


def _evidence_rows(trace: Mapping[str, Any], cited: set[str]) -> list[dict[str, Any]]:
    """Cited evidence as flat fact rows; a year-over-year change becomes its two underlying filed facts."""

    keep = ("ticker", "entity", "metric", "concept", "value", "unit", "start", "end", "form", "filed", "accn",
            "frame", "fiscal_year", "fiscal_period", "derived", "filing_url", "period", "accession", "exhibit_url",
            "sha256", "quote", "highlight_offsets", "context_spans", "low", "high", "provenance")

    def row(result: Mapping[str, Any], ev_id: str, role: str | None = None) -> dict[str, Any]:
        out = {key: result[key] for key in keep if result.get(key) is not None}
        out["id"] = ev_id
        out["tier"] = (result.get("provenance") or {}).get("tier")
        if result.get("exhibit_url"):
            out["filing_url"] = result["exhibit_url"]
            out["quote_start"], out["quote_end"] = result.get("start"), result.get("end")
        if role:
            out["role"] = role
        return out

    rows = []
    for call in trace.get("tool_calls") or []:
        result = call.get("result")
        if not isinstance(result, Mapping) or result.get("evidence_id") not in cited:
            continue
        ev_id = result["evidence_id"]
        if isinstance(result.get("inspected"), list):
            for source in result["inspected"]:
                if isinstance(source, Mapping) and source.get("exhibit_url"):
                    rows.append(row({**source, "ticker": result.get("ticker"), "concept": "Inspected release",
                                     "provenance": {"tier": "L4", "strength": "medium", "furnished": True, "unaudited": True}}, ev_id, "searched"))
            continue
        components = [(result.get(key), role) for key, role in (("current", "current"), ("base", "comparison"))]
        if any(isinstance(component, Mapping) for component, _ in components):
            for component, role in components:
                if isinstance(component, Mapping):
                    rows.append(row(component, ev_id, role))
        else:
            rows.append(row(result, ev_id))
    return rows


def with_report_gaps(report: Mapping[str, Any], report_dir: Path) -> dict[str, Any]:
    """Copy a saved report with gaps computed from its program checks, offline.

    Older checks lack claim_type; recover only that metadata from the saved
    sub-claims. Never substitute the model's numbers for the program's values.
    """

    claims = []
    for item in report["claims"]:
        if not item.get("program_checks"):
            claims.append(dict(item))
            continue
        sub_claims = []
        if any(not check.get("claim_type") for check in item["program_checks"]) and item.get("trace_path"):
            trace = json.loads((report_dir / item["trace_path"]).read_text(encoding="utf-8"))
            sub_claims = (trace.get("final_verdict") or {}).get("sub_claims") or []
        checks = []
        for index, check in enumerate(item["program_checks"]):
            check = dict(check)
            if not check.get("claim_type") and index < len(sub_claims):
                check["claim_type"] = sub_claims[index].get("claim_type")
            check["gap"] = program_check_gap(check)
            checks.append(check)
        claims.append({**item, "program_checks": checks})
    return {**report, "claims": claims}


def refresh_evidence(report_dir: Path) -> dict[str, Any]:
    """Refresh gaps and evidence from saved checks and traces, with no model calls."""

    report_path = report_dir / "report.json"
    report = with_report_gaps(json.loads(report_path.read_text(encoding="utf-8")), report_dir)
    for item in report["claims"]:
        if item.get("status") != "verified" or not item.get("trace_path"):
            continue
        trace = json.loads((report_dir / item["trace_path"]).read_text(encoding="utf-8"))
        cited = {ev for check in item.get("program_checks") or [] for ev in check.get("evidence_ids") or []}
        item["evidence"] = _evidence_rows(trace, cited)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    (report_dir / "report.html").write_text(render_html(report), encoding="utf-8")
    return report


def check_post(
    post: str,
    *,
    client: Any,
    edgar: EdgarClient,
    ledger: Ledger,
    model: str,
    provider: str,
    out_dir: Path,
    max_claims: int = 8,
    secrets: Sequence[str] = (),
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
) -> dict[str, Any]:
    if len(post) > MAX_POST_CHARS:
        raise PostError(f"post is longer than {MAX_POST_CHARS} characters; paste one article section at a time")
    out_dir.mkdir(parents=True, exist_ok=True)
    traces = out_dir / "traces"
    started = time.perf_counter()
    extraction_trace = TraceRecorder("[extraction] " + post[:200], model, provider=provider, secrets=secrets)
    proposed = extract_claims(post, client=client, ledger=ledger, model=model, provider=provider, recorder=extraction_trace)
    extraction_path = write_trace(traces, extraction_trace)
    claims = screen_claims(post, proposed)
    verified = 0
    for item in claims:
        if item["status"] != "to_verify":
            continue
        if verified >= max_claims:
            item.update(status="not_checked", screen_reason=f"over the {max_claims}-claim limit for one post")
            continue
        verified += 1
        recorder = TraceRecorder(item["claim"], model, provider=provider, secrets=secrets)
        result = verify_claim(
            item["claim"], client, edgar, ledger, model, trace=recorder, provider=provider,
            max_output_tokens=max_output_tokens, reasoning_effort=reasoning_effort,
        )
        trace_path = write_trace(traces, recorder)
        trace_dict = recorder.as_dict()
        cited = {ev for check in result.get("program_checks") or [] for ev in check.get("evidence_ids") or []}
        summary = recorder.summary()
        item.update(
            status="verified",
            verdict=result.get("verdict"),
            summary=result.get("summary"),
            evidence_strength=result.get("evidence_strength"),
            flags=result.get("flags") or [],
            program_checks=result.get("program_checks") or [],
            evidence=_evidence_rows(trace_dict, cited),
            cost_usd=summary.get("cost_usd"),
            latency_ms=summary.get("latency_ms"),
            trace_path=str(trace_path.relative_to(out_dir)),
        )
    extraction_cost = extraction_trace.summary().get("cost_usd") or 0.0
    total_cost = extraction_cost + sum(float(item.get("cost_usd") or 0) for item in claims)
    report = {
        "post": post,
        "provider": provider,
        "model": model,
        "extraction_prompt_sha256": hashlib.sha256(EXTRACTION_PROMPT.encode()).hexdigest(),
        "extraction_trace": str(extraction_path.relative_to(out_dir)),
        "proposed_count": len(proposed),
        "claims": claims,
        "counts": {
            status: sum(item["status"] == status for item in claims)
            for status in ("verified", "not_checked", "rejected")
        },
        "verdicts": {
            verdict: sum(item.get("verdict") == verdict for item in claims)
            for verdict in ("supported", "contradicted", "insufficient_evidence")
        },
        "cost_usd": round(total_cost, 6),
        "wall_clock_s": round(time.perf_counter() - started, 1),
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    (out_dir / "report.html").write_text(render_html(report), encoding="utf-8")
    return report


VERDICT_LABEL = {"supported": "Supported", "contradicted": "Contradicted", "insufficient_evidence": "Insufficient evidence"}


def _money(value: Any) -> str:
    if not isinstance(value, (int, float)):
        return "—"
    size = abs(value)
    if size >= 1e9:
        return f"${value / 1e9:,.3f}B"
    if size >= 1e6:
        return f"${value / 1e6:,.2f}M"
    if size < 100:
        return f"{value:g}"
    return f"${value:,.0f}"


def _mark_numbers(text: str) -> str:
    escaped = html.escape(text)
    return re.sub(r"(\$?\d[\d,]*(?:\.\d+)?\s?(?:%|percent|billion|million|trillion|億|萬|元|美元)?)", r'<mark class="n">\1</mark>', escaped)


def _state(item: Mapping[str, Any]) -> str:
    return item.get("verdict") or item["status"]


def render_html(report: Mapping[str, Any]) -> str:
    post = str(report["post"])
    spans = sorted((item for item in report["claims"] if item.get("span")), key=lambda item: item["span"][0])
    pieces, cursor = [], 0
    for item in spans:
        start, end = item["span"]
        if start < cursor:
            continue
        pieces.append(html.escape(post[cursor:start]))
        pieces.append(
            f'<a class="span s-{_state(item)}" href="#c{item["index"]}"><sup>{item["index"]}</sup>{html.escape(post[start:end])}</a>'
        )
        cursor = end
    pieces.append(html.escape(post[cursor:]))
    cards = []
    for item in report["claims"]:
        state = _state(item)
        label = VERDICT_LABEL.get(state) or {"not_checked": "Not checked", "rejected": "Extraction rejected"}.get(state, state)
        steps = ""
        for check in item.get("program_checks") or []:
            steps += (
                '<div class="steps">'
                f'<div><span>Stated</span><b>{_money(check.get("stated_value_used"))}</b> ({html.escape(str(check.get("comparator") or ""))})</div>'
                f'<div><span>SEC value</span><b>{_money(check.get("actual_value"))}</b> {html.escape(", ".join(check.get("evidence_ids") or []))}</div>'
                f'<div><span>Tolerance</span><b>± {_money(check.get("tolerance"))}</b></div>'
                f'<div class="key"><span>Program verdict</span><b>{html.escape(VERDICT_LABEL.get(check.get("program_verdict"), str(check.get("program_verdict"))))}</b></div>'
                "</div>"
            )
        evidence = "".join(
            '<div class="ev">'
            f'<b>{html.escape(str(ev.get("id")))} · {html.escape(str(ev.get("entity") or ev.get("ticker") or ""))}</b> '
            f'<mark class="n">{_money(ev.get("value"))}</mark> · {html.escape(str(ev.get("concept") or ""))} · '
            + (f'L4 · {html.escape(str(ev.get("accession") or ""))} · ' if ev.get("tier") == "L4" else f'{html.escape(str(ev.get("start") or ""))} → {html.escape(str(ev.get("end") or ""))} · ')
            + ("derived from two filed values" if ev.get("derived") else f'{html.escape(str(ev.get("form") or ""))} filed {html.escape(str(ev.get("filed") or ""))}')
            + (f' · <a href="{html.escape(str(ev["filing_url"]))}" target="_blank" rel="noopener">filing on SEC EDGAR</a>' if ev.get("filing_url") else "")
            + render_release_quote(ev)
            + "</div>"
            for ev in item.get("evidence") or []
        )
        note = html.escape(item.get("screen_reason") or item.get("summary") or "")
        cards.append(
            f'<article id="c{item["index"]}" class="card s-{state}">'
            f'<header><span class="idx">{item["index"]}</span><span class="badge">{label}</span></header>'
            f'<p class="quote">“{_mark_numbers(item["quote"])}”</p>'
            f'<p class="claim">Checked as: {_mark_numbers(item["claim"])}</p>'
            f"{steps}{evidence}<p class=\"note\">{note}</p></article>"
        )
    counts, verdicts = report["counts"], report["verdicts"]
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Post Check</title>
<style>
:root{{--bg:#f3f5f7;--sheet:#fff;--ink:#18212b;--muted:#5b6876;--rule:#d5dce3;--ok:#1f7a4d;--okw:#dcefe4;--bad:#b23a32;--badw:#f6dfdc;--warn:#9a6a10;--warnw:#f5ead2;--hl:#fff1b8;--accent:#1d5a86}}
@media (prefers-color-scheme:dark){{:root{{--bg:#11161c;--sheet:#182029;--ink:#e3e9ef;--muted:#97a5b3;--rule:#2c3743;--ok:#6cc799;--okw:#173528;--bad:#ec8a80;--badw:#3d1f1c;--warn:#e2b55a;--warnw:#3a2d12;--hl:#5a4b10;--accent:#7fb6dd;color-scheme:dark}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 "Noto Sans TC",system-ui,sans-serif}}
main{{max-width:880px;margin:0 auto;padding:28px max(16px,env(safe-area-inset-left)) 60px;display:grid;gap:18px}}
h1{{margin:0;font-size:26px}} .meta{{color:var(--muted);font-size:13px}}
.post{{background:var(--sheet);border:1px solid var(--rule);border-radius:6px;padding:18px;white-space:pre-wrap;line-height:1.8}}
.span{{color:inherit;text-decoration:none;border-bottom:3px solid var(--muted);padding:0 2px}}
.span sup{{font:600 10px ui-monospace,monospace;margin-right:2px;color:var(--muted)}}
.s-supported.span{{border-color:var(--ok);background:var(--okw)}} .s-contradicted.span{{border-color:var(--bad);background:var(--badw)}} .s-insufficient_evidence.span{{border-color:var(--warn);background:var(--warnw)}}
.card{{background:var(--sheet);border:1px solid var(--rule);border-left:4px solid var(--muted);border-radius:6px;padding:14px 16px;display:grid;gap:8px}}
.card.s-supported{{border-left-color:var(--ok)}} .card.s-contradicted{{border-left-color:var(--bad)}} .card.s-insufficient_evidence{{border-left-color:var(--warn)}}
.card header{{display:flex;gap:10px;align-items:center}} .idx{{font:600 12px ui-monospace,monospace;color:var(--muted)}}
.badge{{font-weight:700;font-size:13px}} .s-supported .badge{{color:var(--ok)}} .s-contradicted .badge{{color:var(--bad)}} .s-insufficient_evidence .badge{{color:var(--warn)}}
.quote{{margin:0;font-size:16px}} .claim,.note{{margin:0;color:var(--muted);font-size:13px}}
mark.n{{background:var(--hl);color:inherit;padding:0 2px;border-radius:2px;font-family:ui-monospace,monospace;font-size:.92em}}
.steps{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:6px;font-size:13px}}
.steps div{{background:var(--bg);border-radius:4px;padding:6px 8px;display:grid}} .steps span{{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.05em}}
.steps .key{{outline:2px solid var(--accent)}} .ev{{font-size:12.5px;overflow-wrap:anywhere}} a{{color:var(--accent)}}
</style></head><body><main>
<h1>Post check</h1>
<p class="meta">{len(report["claims"])} claims found · {counts["verified"]} verified ({verdicts["supported"]} supported, {verdicts["contradicted"]} contradicted, {verdicts["insufficient_evidence"]} insufficient) · {counts["not_checked"]} not checkable · {counts["rejected"]} rejected · {html.escape(str(report["provider"]))} {html.escape(str(report["model"]))} · ${report["cost_usd"]:.4f} · {report["wall_clock_s"]} s</p>
<div class="post">{"".join(pieces)}</div>
{"".join(cards)}
</main></body></html>
"""
