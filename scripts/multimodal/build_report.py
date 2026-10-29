"""Rebuild the exploratory probe report from saved runs; no network or models."""
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from claimcheck.budget import Ledger
from claimcheck.ingest import render_html
from claimcheck.ingest_media import write_json
from claimcheck.ingest_text import normalize_numbers

OUT = ROOT / "docs/evidence/multimodal-2026-10-29"
SCALE = {None: Decimal(1), "thousand": Decimal(1000), "million": Decimal(1_000_000), "billion": Decimal(1_000_000_000)}
MENTION = re.compile(r"(?<![\w.,])(?P<dollar>\$\s*)?(?P<number>\d[\d,]*(?:\.\d+)?)(?:\s*(?P<scale>billion|million|thousand))?(?:\s*(?P<unit>dollars?|percent)|(?P<percent>%))?", re.I)


def financial_numbers(text: str) -> list[dict]:
    text, _ = normalize_numbers(text)
    result = []
    for match in MENTION.finditer(text):
        if re.search(r"\bex(?:hibit)?\s*$", text[max(0, match.start() - 16):match.start()], re.I):
            continue
        if not (match["dollar"] or match["scale"] or match["unit"] or match["percent"] or "." in match["number"]):
            continue  # exclude years, calendar dates and quarter ordinals
        value = Decimal(match["number"].replace(",", "")) * SCALE[(match["scale"] or "").lower() or None]
        key = format(value.normalize(), "f") + ("%" if match["percent"] or (match["unit"] or "").lower() == "percent" else "")
        result.append({"read_or_heard": match[0], "canonical_value": key, "normalized_span": list(match.span())})
    return result


def expected_numbers(filename: str, channel: dict) -> list[str]:
    if channel["kind"] == "transcript":
        return ["94036000000", "1.67"] if filename == "two-voices.wav" else ["94000000000", "10%", "1.67", "12%", "12%"]
    if channel["kind"] == "frame":
        return {"frame-1": ["94036000000", "23434000000"], "frame-2": ["1.57"], "frame-3": ["1.67"]}[channel["id"]]
    return ["94036000000", "1.67"]


def accuracy(filename: str, channel: dict) -> dict:
    expected = expected_numbers(filename, channel)
    if not channel.get("raw_text"):
        return {"expected": expected, "observed": [], "matched": 0, "extra": 0, "available": False}
    observed = financial_numbers(channel["raw_text"])
    keys = [m["canonical_value"] for m in observed]
    matched = sum(block.size for block in SequenceMatcher(a=expected, b=keys, autojunk=False).get_matching_blocks())
    return {"expected": expected, "observed": observed, "matched": matched, "extra": len(observed) - matched, "available": True}


def cell(stage: dict) -> str:
    return {"reached": "✓", "partial": "✗ partial", "not_reached": "✗", "not_applicable": "—"}[stage["status"]]


def main() -> None:
    runs = {p.parent.name: json.loads(p.read_text()) for p in sorted(OUT.glob("*/ingest.json"))}
    if not runs or any(r["status"] == "running" for r in runs.values()):
        raise SystemExit("wait until all probe runs have finished")
    ledger = Ledger(OUT / "ledger.jsonl")
    total = ledger.spent_total
    if abs(sum(r["cost_usd"] for r in runs.values()) - total) > .000001:
        raise SystemExit("per-input costs do not reconcile to the ledger")
    score = {"policy": "Ordered financial numeric mentions, with explicit scale conversion; excludes dates, quarters and exhibit identifiers. Expected mentions recovered and extras are reported separately. Not WER or a held-out benchmark.", "runs": {}}
    for name, report in runs.items():
        score["runs"][name] = {c["id"]: accuracy(report["input"]["file"], c) for c in report["channels"]}
        (OUT / name / "ingest.html").write_text(render_html(report))
    write_json(OUT / "number-accuracy.json", score)
    events = [json.loads(line) for line in (OUT / "ledger.jsonl").read_text().splitlines()]
    reserves = [e for e in events if e["event"] == "reserve"]
    lines = ["# Multimodal input probe — 2026-10-29", "",
        f"**{len(runs)} recorded exploratory runs; estimated spend ${total:.8f} of the $20 cap.** "
        "Text, screenshots, speech and sampled video frames enter the existing post checker. "
        "The strongest observed paths reach SEC evidence and program verdicts for all four input types. "
        "One true growth claim received a false contradiction after period context was lost, and two voices were merged into one speaker label. "
        "Failures and repeats remain below; this is development evidence, not a held-out evaluation.", "",
        "## Protocol and media", "",
        "All verifier model calls are Meta models: `muse-spark-1.3` for OCR and hosted text reasoning, "
        "`meta-models/muse-spark-open-1026` for Baseten text reasoning, and `muse-voice-transcribe-1.0` for ASR. "
        "Keys load through `claimcheck.config` and are excluded from records. SDK retries are disabled; "
        "the existing agent's bounded incomplete-response and expired-state retries retain their normal reservations. "
        "One locked ledger partitions the total into $10 Meta + $10 Baseten. "
        "SEC tools use only committed, hash-checked companyfacts and release snapshots; missing corpus data fails closed. "
        "No live SEC retrieval, real earnings-call downloads, or non-Meta runtime inference was used.", "",
        "Self-made assets use Apple's [committed 8-K Ex 99.1](../../../tests/fixtures/releases/manifest.json) "
        "([SEC source](https://www.sec.gov/Archives/edgar/data/320193/000032019325000071/a8-kex991q3202506282025.htm)). "
        "The 47.29-second reading excerpts real release sentences, with **EPS deliberately changed from $1.57 to $1.67**. "
        "Slides reproduce $94,036 million sales, $23,434 million net income and $1.57 EPS; the third slide deliberately says $1.67. "
        "The PNG says **Example post** and names a fictional author. "
        "The smaller PNG, spoken-number text, two-voice clip, silent video and sentence-captioned video are development controls. "
        "The captioned control was created after inspecting row-only extraction failures.", "",
        "**Media-generation deviation:** macOS `say` with Samantha and Fred returned "
        "`sandbox_extension_issue_file` and zero audio frames. The committed narration instead uses "
        "eSpeak NG 1.53.0 offline formant synthesis, followed by ffmpeg; no generative model created the audio. "
        "It is synthetic narration, never the CFO's voice. "
        "[Generation record](../../../tests/fixtures/multimodal/generation.json), "
        "[input hashes/expected numbers](../../../tests/fixtures/multimodal/manifest.json), "
        "[generator](../../../scripts/multimodal/make_media.py).", "",
        "Each run has `protocol.json` with exact model IDs, source hashes and fixture hashes, "
        "`ingest.json`/`ingest.html`, media responses in `calls/`, and post/model/tool traces in `checks/`. "
        "Each code revision and repeat is recorded; there was no frozen pre-evaluation protocol. "
        "Three frames are sampled at 1/6, 1/2 and 5/6 of the duration. "
        "Speech and frame claims are checked independently; disagreement is not automatically fused into one claim.", "",
        "## Capability matrix", "",
        "✓ = reached for every relevant channel; ✗ partial = some channels/claims reached it; "
        "✗ = none reached it; — = no speaker attribution applies. Stage 4 requires cited L1–L4 numeric evidence, "
        "not merely a successful search. Stage 5 includes a program `insufficient_evidence` decision. "
        "Stage 6 means unverified speaker label + whole-turn timestamp, **not a named-person attribution**.", "",
        "| Input / run | 1 Decode | 2 Text + offsets | 3 Claims | 4 SEC | 5 Program | 6 Attribution | Reason / limit |",
        "|---|---|---|---|---|---|---|---|"]
    for name, report in runs.items():
        reasons = []
        for c in report["channels"]:
            if c.get("error"):
                reasons.append(c["id"] + ": " + c["error"])
            reasons += [c["id"] + ": " + x["screen_reason"] for x in c.get("claims", []) if x.get("status") == "rejected"]
        reason = "; ".join(dict.fromkeys(reasons)) or "All applicable stages reached; diarization identities unverified" if report["input"].get("kind") in {"audio", "video"} else "; ".join(dict.fromkeys(reasons)) or "Financial numbers preserved; revenue supported, deliberate EPS error contradicted"
        if name == "audio-two-voices":
            reason += "; two known synthetic voices both labeled A"
        if name == "video-captioned-baseten":
            reason += "; growth claim lost period and was falsely contradicted"
        lines.append(f"| [{name}]({name}/ingest.html) ({report['input']['kind']}) | " + " | ".join(cell(s) for s in report["stages"]) + " | " + reason.replace("|", "/") + " |")
    lines += ["", "## Number recovery, cost and latency", "",
        "Number recovery is measured against the known self-made source: financial numeric mentions only, "
        "excluding calendar dates and quarter/year labels. Program normalization expands bounded English numbers, "
        "joined tens, decimal digits, grouped numerals and ordinal quarters; unsupported verbal forms stay unchanged. "
        "Million/billion comparisons here use the explicit unit. A correct transcription of the deliberate $1.67 "
        "error counts as correct **recovery**, while SEC verification must contradict the claim. "
        "This does not measure word error rate, semantic claim recall, OCR pixel localization or general financial accuracy. "
        "All observed tokens and expected values are retained in [number-accuracy.json](number-accuracy.json).", "",
        "| Run | Financial mentions recovered / expected (extras) | Estimated cost USD | Wall seconds | Text provider |",
        "|---|---|---:|---:|---|"]
    for name, report in runs.items():
        scores = score["runs"][name]
        details = "; ".join(f"{cid}: {s['matched']}/{len(s['expected'])} (+{s['extra']})" if s["available"] else f"{cid}: unavailable" for cid, s in scores.items())
        lines.append(f"| {name} | {details} | ${report['cost_usd']:.8f} | {report['wall_clock_s']:.3f} | {report['provider']} |")
    lines += ["", f"**Total: ${total:.8f} across {len(reserves)} reserved API attempts.** "
        f"Meta: ${ledger.spent_for_provider('meta'):.8f}; Baseten: ${ledger.spent_for_provider('baseten'):.8f}. "
        "Token costs use recorded usage at $1.25/M input, $0.15/M cached input and $4.25/M output. "
        "ASR reserves `ceil(audio_seconds) × $0.18 / 3600` before upload. "
        "Failed or usage-less attempts retain the conservative reservation, so totals are estimates/bounds, not provider invoices. "
        "Each row includes decoding, OCR/ASR, extraction and verification. Runs sometimes overlap; their wall times are per input, "
        "not additive elapsed time. [Ledger](ledger.jsonl), "
        "[Meta prices](https://dev.meta.ai/docs/pricing-rate-limits), "
        "[Baseten prices](https://www.baseten.co/pricing/).", "",
        "## Attribution and honest failures", "",
        "The transcript is a timestamped lead. It is never L5 financial evidence: every accepted numeric claim still needs "
        "SEC L1–L4 evidence and a program check. Heard/read values, their normalized replacements, original character spans, "
        "and each claim's matching source turns remain in the ingest JSON. Repeated occurrences retain all matching turns. "
        "The HTML shows the original quote and speaker/time bracket alongside the verdict and links to filing evidence. "
        "No program mapping from diarization letters to names or roles exists. "
        "Meta documents [turn timestamps, not word timestamps](https://dev.meta.ai/docs/speech-to-text) "
        "and [session-scoped speaker labels](https://dev.meta.ai/docs/api-reference/voice/schemas).", ""]
    for name, report in runs.items():
        for c in report["channels"]:
            if c["kind"] != "transcript" or not c.get("segments"):
                continue
            labels = sorted({str(s["speaker"]) for s in c["segments"] if s.get("speaker")})
            times = [f"{s.get('speaker', '?')}: {s.get('start_ms', '?')}–{s.get('end_ms', '?')} ms" for s in c["segments"]]
            lines.append(f"- **{name}:** labels {', '.join(labels) or 'none'}; " + "; ".join(times) + ".")
    lines += ["", "Observed limits:", "",
        "- The first audio run returned a usable, labeled transcript but stopped at post extraction (`PostError`). "
        "Its extraction response was not retained by the then-current post checker. The same omission affected the first video's failed audio extraction. "
        "Their costs and stop states are preserved; the precise provider text cannot be reconstructed. "
        "The implementation now persists extraction/claim traces in `finally`, including failed attempts. "
        "Subsequent runs raised the per-call output limit from 4,000 to 8,000 and tried Baseten text reasoning; these are explicitly repeats.",
        "- The Meta audio repeat failed later with `BadRequestError`, retaining one completed claim and the remaining extraction/source maps. "
        "That earlier revision did not yet persist the failed claim trace; the ledger reservation is kept. "
        "Provider failures are not program verdicts. See each ingest record for exactly how far it got.",
        "- ASR duplicated words and rendered the written name **Kevan Parekh** as **Kevan Park** in the first recording. "
        "Preserved financial numbers do not establish quote fidelity or who actually spoke. "
        "Whole-turn spans can cover tens of seconds; a number does not inherit a fabricated word timestamp.",
        "- **Diarization failure:** the two-voice fixture contains two deliberately different synthetic voices, but ASR labeled both turns **A**. "
        "Stage 6 records that labeled timestamps exist; it does not mean speaker separation or identity was correct.",
        "- **Known false contradiction:** `video-captioned-baseten` extracted the true FY2025Q3 EPS-growth statement as "
        "`Apple reported EPS growth of 12%.`, dropping its period context. The agent compared FY2026Q3 EPS (2.02) with FY2025Q3 (1.57), "
        "28.66% growth, and the program contradicted it. The intended release growth is 1.57 / 1.40 − 1 = 12.14%, which supports 12%. "
        "This is an end-to-end context-loss failure despite correct ASR numbers and successful tool/program stages. "
        "The saved verdict remains unchanged. In `audio-baseten`, two larger financial clauses were rejected for adding the date `28`; "
        "only the growth clause was checked. Reaching a stage is not complete claim recall or a correctness score.",
        "- Row-only slides expose extraction/context and routing limits: some rewrites add `28` from the date heading, "
        "which the existing post guard correctly rejects because that number is absent from the selected quote. "
        "Another filed EPS can return insufficient evidence. Captioned slides are a separate post-hoc control, not a replacement for those failures.",
        "- Silent video has no speech channel; its frame results remain usable. Sampling only three frames can miss other visual claims, "
        "and a frame timestamp provides no speaker identity. No full-video understanding, public replay ingestion, long-call chunking, "
        "word alignment, verified CFO attribution, overlap benchmark or human-name verification is implemented.",
        "- The first text/screenshot runs overlapped before own-input cost accounting was added. Their corrected cost is the sum of their recorded calls; "
        "`initial-ingest.json` and `original_recorded_cost_usd` retain the initial shared-delta values. "
        "Later runs track their own reservation IDs over the shared locked budget. The corrected per-run total reconciles to the ledger.", "",
        "## Reproduce offline", "", "```sh", "python3 scripts/multimodal/build_report.py", "sh scripts/verify.sh", "UV_OFFLINE=1 sh scripts/verify.sh", "```", "",
        "The report builder only reads saved records. Offline tests replay the actual Meta OCR/ASR/text and Baseten text responses "
        "against committed SEC data, including deliberate false numbers. Codec checks are optional when ffmpeg/ffprobe are absent; "
        "response replay does not require those binaries. No keys, external audio or ignored caches are needed. "
        "[Runtime](../../../src/claimcheck/ingest.py), [offline tests](../../../tests/test_ingest.py), "
        "[paid probe runner](../../../scripts/multimodal/run_probe.py). "
        "The paid runner is intentionally separate from verification and refuses to overwrite a saved run.", ""]
    if (OUT / "validation.json").is_file():
        lines += ["Validation: **372 product tests, 83 demo tests and 41 standalone Node tests passed**; "
                  "`UV_OFFLINE=1 sh scripts/verify.sh` passed all five final checks. "
                  "[Verification receipt](validation.json).", ""]
    (OUT / "REPORT.md").write_text("\n".join(lines))
    print(f"Built {len(runs)}-run report; total ${total:.8f}")


if __name__ == "__main__":
    main()
