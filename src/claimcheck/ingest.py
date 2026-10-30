"""Ingest a local post, screenshot, audio clip or video into the post checker.

Each channel retains heard/read text, a reversible offset map, and independent
stage outcomes. Audio attribution is a session label and a whole ASR turn, never
a verified executive identity. Frames and speech are checked separately.
"""
from __future__ import annotations

import html
import re
import time
from pathlib import Path
from typing import Any, Sequence

from .budget import BudgetExceeded, Ledger, UnknownModel
from .ingest_media import MAX_BYTES, IngestError, decode, input_kind, read_image, sha256, transcribe, write_json
from .ingest_text import normalize_numbers, original_offset
from .post import PostError, check_post
from .providers import BASETEN_DEFAULT_MODEL, FIREWORKS_DEFAULT_MODEL, META_DEFAULT_MODEL
from .trace import redact

STAGES = (
    "input decoded", "text/transcript obtained with source offsets", "claims extracted",
    "SEC evidence found (L1–L4)", "program verdict", "timestamp and speaker attribution",
)
META_MODELS = {
    "meta": {META_DEFAULT_MODEL, "muse-wonder-1.0"},
    "baseten": {BASETEN_DEFAULT_MODEL},
    "fireworks": {FIREWORKS_DEFAULT_MODEL},
}


class _InputLedger:
    """Own-call accounting over the shared, locked provider budget ledger.

    Other ingests may use the same budget concurrently; their charges must not
    appear in this input's cost/latency report. Failed calls keep reservations.
    """
    def __init__(self, parent: Ledger) -> None:
        self.parent = parent
        self.amounts: dict[str, float] = {}
        self.cost_records: dict[str, dict[str, Any]] = {}
        self.stage = "unclassified"


    @property
    def spent_total(self) -> float:
        return sum(self.amounts.values())

    def reserve(self, *args: Any, **kwargs: Any) -> Any:
        reservation = self.parent.reserve(*args, **kwargs)
        self.amounts[reservation.reservation_id] = reservation.amount
        self.cost_records[reservation.reservation_id] = {
            "stage": self.stage, "provider": reservation.provider, "model": reservation.model,
            "reserved_usd": reservation.amount, "estimated_usd": reservation.amount,
            "basis": "retained_reservation"}
        return reservation

    def reserve_audio(self, duration_s: float) -> Any:
        reservation = self.parent.reserve_audio(duration_s)
        self.amounts[reservation.reservation_id] = reservation.amount
        self.cost_records[reservation.reservation_id] = {
            "stage": self.stage, "provider": reservation.provider, "model": reservation.model,
            "reserved_usd": reservation.amount, "estimated_usd": reservation.amount,
            "basis": "retained_reservation"}
        return reservation

    def reconcile(self, reservation: Any, usage: Any = None) -> float:
        amount = self.parent.reconcile(reservation, usage)
        self.amounts[reservation.reservation_id] = amount
        record = self.cost_records[reservation.reservation_id]
        record["estimated_usd"] = amount
        # Consult the authoritative reconciliation event, not amount differences.
        events = self.parent._events()
        event = next((e for e in reversed(events) if e.get("event") == "reconcile"
                      and e.get("reservation_id") == reservation.reservation_id), None)
        record["basis"] = "usage_estimate" if event and not event.get("usage_missing") else "retained_reservation"
        return amount

    def cost_summary(self) -> dict[str, Any]:
        stages: dict[str, float] = {}
        for record in self.cost_records.values():
            stages[record["stage"]] = stages.get(record["stage"], 0.0) + record["estimated_usd"]
        return {"currency": "USD", "billed_usd": None,
                "estimated_or_reserved_usd": self.spent_total,
                "original_reservations_usd": sum(r["reserved_usd"] for r in self.cost_records.values()),
                "by_stage_usd": stages, "attempts": self.cost_records,
                "price_basis": "Configured ledger rates; not a provider invoice. Failed/usage-less reservations retained; retries included.",
                "asr_reserved_usd_per_hour": 0.18,
                "rates": {str(k): dict(v) for k, v in self.parent.model_prices.items()}}



def _stage(number: int, status: str, reason: str) -> dict[str, Any]:
    return {"stage": number, "name": STAGES[number - 1], "status": status, "reason": reason}


def prepare_text(channel: dict[str, Any]) -> None:
    parts, cursor = [], 0
    for segment in channel["segments"]:
        if parts:
            parts.append("\n\n")
            cursor += 2
        text = segment["text"]
        segment["raw_span"] = [cursor, cursor + len(text)]
        parts.append(text)
        cursor += len(text)
    raw = "".join(parts)
    normalized, edits = normalize_numbers(raw)
    channel.update(raw_text=raw, normalized_text=normalized, number_normalizations=edits,
                   numeric_source="heard" if channel["kind"] == "transcript" else "read",
                   number_policy="Observed input values only; program normalization precedes extraction. SEC evidence is separate.")


def attach_locations(channel: dict[str, Any], claims: list[dict[str, Any]]) -> None:
    """Map every occurrence, including repeated quotes, back to original turns."""
    normalized = channel["normalized_text"]
    raw = channel["raw_text"]
    for claim in claims:
        locations = []
        if claim.get("span") and claim.get("quote"):
            pattern = r"\s+".join(re.escape(w) for w in claim["quote"].split())
            spans = claim.get('quote_spans')
            if spans is None:
                spans = [list(m.span()) for m in re.finditer(pattern, normalized)]
            for a, b in spans:
                start = original_offset(a, channel["number_normalizations"])
                end = original_offset(b, channel["number_normalizations"], end=True)
                sources = []
                for segment in channel["segments"]:
                    a, b = segment["raw_span"]
                    if start < b and end > a:
                        source = {key: segment[key] for key in ("id", "start_ms", "end_ms", "speaker", "sample_ms", "timing", "page") if key in segment}
                        source.update(segment_span=segment["raw_span"], overlap_span=[max(a, start), min(b, end)])
                        if "speaker" in source:
                            source["identity"] = "unverified session-scoped diarization label"
                        sources.append(source)
                locations.append({"raw_span": [start, end], "heard_or_read_quote": raw[start:end], "sources": sources})
        claim["source_locations"] = locations
        context = claim.get('period_context')
        if context:
            a, b = context['span']
            start = original_offset(a, channel['number_normalizations'])
            end = original_offset(b, channel['number_normalizations'], end=True)
            context.update(raw_span=[start, end], heard_or_read=raw[start:end],
                sources=[{k: s[k] for k in ('id', 'start_ms', 'end_ms', 'speaker', 'sample_ms', 'timing', 'page') if k in s}
                         for s in channel['segments'] if start < s['raw_span'][1] and end > s['raw_span'][0]])


def channel_stages(channel: dict[str, Any]) -> list[dict[str, Any]]:
    claims = channel.get("claims", [])
    accepted = [c for c in claims if c.get("status") != "rejected" and c.get("kind") in {"reported_fact", "issuer_guidance"}]
    verified = [c for c in claims if c.get("program_checks")]
    evidence = [e for c in claims for e in c.get("evidence", [])
                if e.get("tier") in {"L1", "L2", "L3", "L4"} and e.get("role") != "searched"]
    timed = [c for c in accepted if c.get("source_locations") and all(
        loc["sources"] and all("start_ms" in s and "end_ms" in s and s.get("speaker") for s in loc["sources"])
        for loc in c["source_locations"])]
    error = channel.get("error", "not reached")
    stages = [
        _stage(1, "reached" if channel.get("decoded") else "not_reached", "local file decoded" if channel.get("decoded") else error),
        _stage(2, "reached" if channel.get("raw_text", "").strip() else "not_reached", "original text and character offsets retained" if channel.get("raw_text", "").strip() else error),
        _stage(3, "reached" if accepted else "not_reached", f"{len(accepted)} accepted numeric claims; {len(claims)} proposals screened" if "claims" in channel else error),
        _stage(4, "reached" if evidence else "not_reached", "cited " + ", ".join(sorted({e["tier"] for e in evidence})) if evidence else "no cited SEC numeric evidence"),
        _stage(5, "reached" if verified and len(verified) == len(accepted) else "partial" if verified else "not_reached", f"{len(verified)}/{len(accepted)} accepted claims have program checks; insufficient evidence is a verdict"),
    ]
    if channel["kind"] != "transcript":
        stages.append(_stage(6, "not_applicable", "text/images do not establish who spoke; a sampled frame time is not speech attribution"))
    else:
        status = "reached" if timed and len(timed) == len(accepted) else "partial" if timed else "not_reached"
        stages.append(_stage(6, status, f"{len(timed)}/{len(accepted)} claims mapped to labeled ASR turns; names/roles unverified; no word timestamps"))
    return stages


def coverage_summary(channels: list[dict[str, Any]]) -> dict[str, Any]:
    """Operational counts, never an estimate of unknown input-claim recall."""
    claims = [claim for channel in channels for claim in channel.get("claims", [])]
    accepted = [claim for claim in claims if claim.get("status") != "rejected"
                and claim.get("kind") in {"reported_fact", "issuer_guidance"}]
    checked = [claim for claim in accepted if claim.get("program_checks")]
    return {
        "channels": len(channels),
        "channels_with_errors": sum(bool(c.get("error")) for c in channels),
        "proposed_claims": len(claims),
        "accepted_claims": len(accepted),
        "program_checked_claims": len(checked),
        "accepted_without_program_checks": len(accepted) - len(checked),
        "rejected_claims": sum(c.get("status") == "rejected" for c in claims),
        "failed_claims": sum(c.get("status") == "failed" for c in claims),
        "insufficient_evidence_claims": sum(c.get("verdict") == "insufficient_evidence" for c in accepted),
        "full_content_recall": None,
        "note": "Counts describe extracted claim rows, not unique facts or all input assertions. "
                "Full-content recall is unknown without an independently labeled denominator. "
                "Program-checked includes insufficient-evidence verdicts and does not mean supported.",
    }


def aggregate_stages(channels: list[dict[str, Any]], error: str = "", kind: str | None = None) -> list[dict[str, Any]]:
    result = []
    for n in range(1, 7):
        relevant = [c["stages"][n - 1] for c in channels if c["stages"][n - 1]["status"] != "not_applicable"]
        states = [s["status"] for s in relevant]
        status = ("reached" if states and all(s == "reached" for s in states) else "partial" if any(s in {"reached", "partial"} for s in states)
                  else "not_reached" if states or n < 6 or kind in {"audio", "video"} else "not_applicable")
        reasons = "; ".join(f"{c['id']}: {c['stages'][n - 1]['reason']}" for c in channels
                            if c["stages"][n - 1]["status"] != "not_applicable")
        result.append(_stage(n, status, reasons or error or "not applicable"))
    return result


def ingest_file(path: Path, *, client: Any, edgar: Any, ledger: Ledger, model: str,
                provider: str, out_dir: Path, vision_client: Any = None, asr_http: Any = None,
                meta_api_key: str | None = None, max_claims: int = 8, secrets: Sequence[str] = (),
                max_output_tokens: int | None = None, reasoning_effort: str | None = None,
                release_client: Any = None, source_ticker: str | None = None) -> dict[str, Any]:
    if model not in META_MODELS.get(provider, set()):
        raise IngestError("ingest permits only the configured Meta Muse model IDs")
    if source_ticker and not re.fullmatch(r'[A-Z][A-Z0-9.-]{0,9}', source_ticker):
        raise IngestError('invalid source ticker context')
    if max_claims < 1:
        raise IngestError("max_claims must be positive")
    if (out_dir / "ingest.json").exists():
        raise IngestError("output already contains ingest.json; choose a new output directory")
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger = _InputLedger(ledger)
    started, spent_before = time.perf_counter(), ledger.spent_total
    all_secrets = [*secrets, *([meta_api_key] if meta_api_key else [])]
    report: dict[str, Any] = {"schema_version": 1, "input": {"file": path.name}, "channels": [],
        "provider": provider, "model": model, "errors": [], "status": "running",
        "limitations": ["Heard/read numbers are input claims, never filing evidence.",
            "Audio timestamps describe ASR turns, not individual words; speaker labels are not names or roles.",
            "Video samples three frames at 1/6, 1/2 and 5/6 of duration; unsampled visuals can be missed.",
            "Audio and frame claims are checked independently; no cross-modal identity or truth inference.",
            "PDF uses native page text only; reading order/table fidelity is not guaranteed, scanned pages are not checked, and context is not propagated across pages."]}

    if source_ticker:
        report['source_context'] = {'ticker_hint': source_ticker, 'authenticated': False}
        report['limitations'].append(f'User-supplied ticker hint {source_ticker} is not issuer authentication. Extraction selects at most {max_claims} claims per window; unselected content remains unchecked.')

    def save() -> None:
        from .policy import policy_for
        report["verification_policy"] = policy_for(edgar).to_dict()
        for channel in report["channels"]:
            channel["stages"] = channel_stages(channel)
        report["stages"] = aggregate_stages(report["channels"], "; ".join(report["errors"]), report["input"].get("kind"))
        report["coverage"] = coverage_summary(report["channels"])
        from .coverage_diagnostics import coverage_diagnostics
        report["coverage_diagnostics"] = coverage_diagnostics(report["channels"])
        report["cost_breakdown"] = ledger.cost_summary()
        report["cost_usd"] = round(ledger.spent_total - spent_before, 8)
        report["reservation_ids"] = list(ledger.amounts)
        report["wall_clock_s"] = round(time.perf_counter() - started, 3)
        write_json(out_dir / "ingest.json", report, all_secrets)
        (out_dir / "ingest.html").write_text(render_html(redact(report, all_secrets)), encoding="utf-8")

    try:
        report["input"]["kind"] = input_kind(path)
        if path.is_file() and path.stat().st_size <= MAX_BYTES:
            report["input"].update(sha256=sha256(path), bytes=path.stat().st_size)
        kind, channels = decode(path, out_dir / "media")
        report["input"]["kind"] = kind
        report["channels"] = channels
        save()
        for channel in channels:
            channel_started, channel_spent = time.perf_counter(), ledger.spent_total
            earlier_reservations = set(ledger.amounts)
            call_path = out_dir / "calls" / (channel["id"] + ".json")
            try:
                if not channel["decoded"]:
                    continue
                ledger.stage = "asr" if channel["kind"] == "transcript" else "ocr"
                if channel["kind"] == "transcript":
                    if not meta_api_key or asr_http is None:
                        raise IngestError("Meta ASR key/client unavailable")
                    channel["segments"], _ = transcribe(channel, http=asr_http, api_key=meta_api_key, ledger=ledger, record=call_path)
                    channel["media_call"] = str(call_path.relative_to(out_dir))
                elif channel["kind"] in {"ocr", "frame"}:
                    if vision_client is None:
                        raise IngestError("Meta vision client unavailable")
                    channel["segments"], _ = read_image(channel, client=vision_client, ledger=ledger, record=call_path, secrets=all_secrets)
                    channel["media_call"] = str(call_path.relative_to(out_dir))
                prepare_text(channel)
                save()
                if client is None:
                    raise IngestError("text extraction/checking client unavailable; configure the selected provider key")

                def progress(claims: list[dict[str, Any]]) -> None:
                    attach_locations(channel, claims)
                    channel["claims"] = claims
                    save()

                post_dir = out_dir / "checks" / channel["id"]
                result = check_post(channel["normalized_text"], client=client, edgar=edgar, ledger=ledger,
                    model=model, provider=provider, out_dir=post_dir, max_claims=max_claims, secrets=all_secrets,
                    max_output_tokens=max_output_tokens, reasoning_effort=reasoning_effort,
                    release_client=release_client, on_progress=progress,
                    extraction_max_output_tokens=max_output_tokens or 4000, allow_long_input=True,
                    **({'source_ticker': source_ticker, 'bounded_extraction': True, 'extraction_reasoning_effort': 'low'} if source_ticker else {}))
                attach_locations(channel, result["claims"])
                channel.update(claims=result["claims"], post_report=str((post_dir / "report.html").relative_to(out_dir)),
                               extraction_windows=result['extraction_windows'], claim_limit=result['claim_limit'],
                               extraction_scope=result.get('extraction_scope'), source_context=result.get('source_context'),
                               post_cost_usd=result["cost_usd"], extraction_trace=str((post_dir / result["extraction_trace"]).relative_to(out_dir)))
                if any(c['status'] == 'failed' for c in result['claims']):
                    channel['error'] = 'one or more claims failed; see retained claim traces'
                # Source maps belong in both the machine report and the ingest view.
                write_json(post_dir / "report.json", result, all_secrets)
            except Exception as exc:
                channel["error"] = str(exc) if isinstance(exc, (IngestError, PostError, BudgetExceeded, UnknownModel)) else f"pipeline failed ({type(exc).__name__})"
                if isinstance(getattr(exc, "status_code", None), int):
                    channel["http_status"] = exc.status_code
                if call_path.is_file():
                    channel["media_call"] = str(call_path.relative_to(out_dir))
            finally:
                channel["cost_usd"] = round(ledger.spent_total - channel_spent, 8)
                channel["reservation_ids"] = [rid for rid in ledger.amounts if rid not in earlier_reservations]
                channel["retained_traces"] = [str(p.relative_to(out_dir)) for p in sorted((out_dir / "checks" / channel["id"] / "traces").glob("*.json"))]
                channel["wall_clock_s"] = round(time.perf_counter() - channel_started, 3)
                # Paths in committed records are portable and relative to the report.
                for key in ("image", "audio"):
                    if key in channel:
                        channel[key] = str(Path(channel[key]).relative_to(out_dir))
                for chunk in channel.get('audio_chunks', []):
                    chunk['audio'] = str(Path(chunk['audio']).relative_to(out_dir))
                save()
        report["status"] = "partial" if any(c.get("error") for c in channels) else "completed"
    except Exception as exc:
        report["errors"].append(str(exc) if isinstance(exc, (IngestError, BudgetExceeded, UnknownModel)) else f"input failed ({type(exc).__name__})")
        report["status"] = "failed"
    finally:
        save()
    return redact(report, all_secrets)


def _time(ms: int) -> str:
    return f"{ms // 60000:02d}:{ms // 1000 % 60:02d}.{ms % 1000:03d}"


def render_html(report: dict[str, Any]) -> str:
    esc = lambda value: html.escape(str(value))
    rows = "".join(f"<tr><td>{s['stage']}. {esc(s['name'])}</td><td>{esc(s['status'])}</td><td>{esc(s['reason'])}</td></tr>" for s in report.get("stages", []))
    from .policy import policy_html
    policy_description = policy_html(report)
    costs = report.get("cost_breakdown", {})
    cost_html = "<section><h2>Cost breakdown (USD)</h2><ul>" + "".join(
        f"<li>{esc(stage)}: ${amount:.6f}</li>" for stage, amount in costs.get("by_stage_usd", {}).items()) + "</ul><p>Provider bill: not reconciled. Estimates include retained reservations and retries.</p></section>"
    from .coverage_diagnostics import coverage_diagnostics
    diagnostic_html = "<section><h2>Coverage gaps and next steps</h2>" + "".join(
        f"<p><strong>{esc(d['channel_id'])}: {esc(d['code'])}</strong> — {esc(d['message'])} {esc(d['next_step'])}</p>"
        for d in coverage_diagnostics(report["channels"])) + "</section>"
    coverage = coverage_summary(report["channels"])
    coverage_html = (
        f"<section><h2>What was checked</h2><p>{coverage['proposed_claims']} proposed · "
        f"{coverage['accepted_claims']} accepted · {coverage['program_checked_claims']} program-checked · "
        f"{coverage['accepted_without_program_checks']} accepted without program checks · "
        f"{coverage['failed_claims']} failed · {coverage['rejected_claims']} rejected.</p>"
        f"<p>{coverage['channels_with_errors']} channels have errors. "
        f"{coverage['insufficient_evidence_claims']} accepted claims have insufficient evidence.</p>"
        f"<p><strong>Full-content recall: unknown.</strong> {esc(coverage['note'])}</p></section>"
    )
    blocks = []
    for channel in report["channels"]:
        claims = []
        for claim in channel.get("claims", []):
            sources = []
            for loc in claim.get("source_locations", []):
                labels = []
                for source in loc["sources"]:
                    if "start_ms" in source:
                        labels.append(f"speaker {source.get('speaker', 'unknown')} (unverified), {_time(source['start_ms'])}–{_time(source['end_ms'])}; whole turn")
                    elif "sample_ms" in source:
                        labels.append(f"frame sampled at {_time(source['sample_ms'])}; speaker unknown")
                    elif "page" in source:
                        labels.append(f"PDF page {source['page']}; extracted-text characters {loc['raw_span'][0]}–{loc['raw_span'][1]}")
                    else:
                        labels.append(f"source characters {loc['raw_span'][0]}–{loc['raw_span'][1]}")
                sources.append(f"<p>{esc('; '.join(labels))}</p><blockquote>{esc(loc['heard_or_read_quote'])}</blockquote>")
            trace = f"<a href='checks/{esc(channel['id'])}/{esc(claim['trace_path'])}'>model/tool trace</a>" if claim.get("trace_path") else ""
            context = claim.get('period_context')
            context_html = f"<p>Period context ({esc(context['scope'])}): {esc(context['heard_or_read'])}; source characters {context['raw_span'][0]}–{context['raw_span'][1]}</p>" if context and 'raw_span' in context else ''
            reason = claim.get('summary') or claim.get('screen_reason') or claim.get('error') or ''
            claims.append(f"<li><b>{esc(claim.get('verdict') or claim['status'])}</b>: {esc(claim['claim'])}<p>{esc(reason)}</p>{context_html}{''.join(sources)}{trace}</li>")
        link = f"<p><a href='{esc(channel['post_report'])}'>SEC evidence and program checks</a></p>" if channel.get("post_report") else ""
        blocks.append(f"<section><h2>{esc(channel['id'])}</h2><p>{esc(channel.get('error', ''))}</p><details><summary>Original heard/read text</summary><pre>{esc(channel.get('raw_text', ''))}</pre></details><ul>{''.join(claims)}</ul>{link}</section>")
    return f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Input probe</title>
<style>body{{max-width:1000px;margin:32px auto;padding:0 20px;font:16px/1.5 system-ui;color:#18212b;background:#f8f8f5}}table{{border-collapse:collapse;width:100%}}td,th{{padding:10px;text-align:left;border:1px solid #ccc}}pre{{white-space:pre-wrap}}section{{margin:32px 0}}blockquote{{border-left:3px solid #789;padding-left:16px}}li{{margin:20px 0}}</style>
<h1>Input probe: {esc(report['input']['file'])}</h1><p>{esc(report['status'])} · ${report.get('cost_usd', 0):.6f} · {report.get('wall_clock_s', 0)} s</p>
<p>Read/heard values require SEC evidence. Speaker labels are unverified, session-scoped labels. Timestamps cover whole turns, not individual words.</p>
{policy_description}{cost_html}{coverage_html}{diagnostic_html}<p>{esc("; ".join(report.get("limitations", [])))}</p><table><tr><th>Stage</th><th>Outcome</th><th>Reason</th></tr>{rows}</table>{''.join(blocks)}<p>{esc('; '.join(report['errors']))}</p></html>"""
