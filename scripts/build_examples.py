#!/usr/bin/env python3
"""Build the 15 published examples, offline by default.

Only --synthesize calls the host's locked Breeze clone. --render-media encodes
retained WAVs with FFmpeg. Neither operation runs during normal build/--check.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs/examples"
KINDS = {"text": "txt", "image": "png", "pdf": "pdf", "audio": "mp3", "video": "mp4"}
SIZE = (1280, 720)
MAX_BYTES = 2_000_000
MAX_SECONDS = 20
FONT = "fonts/NotoSerifTC-Regular-latin.ttf"
REF_SHA256 = "43346fa72fb56df38918f318012c0cf2856fba03728b18544d0a864d50f6a6c4"
REF_TEXT = ("This is Market Claim Verifier. Paste a finance post, and every number is checked against the company's "
            "own SEC filings, with a link to the exact line that proves it.")
HOST_COMMAND = ("uv run --frozen python scripts/build_examples.py --synthesize --device mps "
                "--video-repo /Users/yan/git/market-claim-verifier-video "
                "--breeze /Users/yan/ml-engines/breeze-tts")
DESCRIPTIONS = {
    "text": {"en": "The original self-made post.", "zh": "自行撰寫的原始貼文。"},
    "image": {"en": "The same post as an image; Muse OCR reads the visible text.", "zh": "同一貼文的圖片，由 Muse OCR 讀取畫面文字。"},
    "pdf": {"en": "A one-page PDF with selectable native text.", "zh": "單頁 PDF，含可選取的原生文字。"},
    "audio": {"en": "The same post read by the locked Breeze clone; Muse transcribes it.", "zh": "鎖定的 Breeze 聲音朗讀同一貼文，再由 Muse 轉錄。"},
    "video": {"en": "The post image with that narration; Muse reads frames and audio.", "zh": "貼文圖片搭配同一旁白；Muse 讀取影格與音軌。"},
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def put(path, raw, check=False):
    if check:
        if not path.is_file() or path.read_bytes() != raw:
            raise ValueError(f"Stale example: {path.relative_to(EXAMPLES)}")
    elif not path.is_file() or path.read_bytes() != raw:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def load_stories():
    """Resolve every number against the registered, hash-checked SEC snapshots."""
    spec = json.loads((EXAMPLES / "stories.json").read_text())
    provenance_path = ROOT / "tests/fixtures/sec-offline/provenance.json"
    provenance_raw = provenance_path.read_bytes()
    if digest(provenance_raw) != spec["provenance_sha256"]:
        raise ValueError("SEC provenance changed; review the story sources")
    provenance = json.loads(provenance_raw)
    if [s["id"] for s in spec["stories"]] != ["a", "b", "c"]:
        raise ValueError("Expected exactly stories a, b, c")
    for story in spec["stories"]:
        if not 0 < len(story["text"]) <= 600 or not story["text"].isascii():
            raise ValueError("Story text must be ASCII and <=600 characters")
        displayed = re.findall(r"\$[\d,.]+\s+\w+", story["text"])
        cited = [n["displayed_text"] for n in story["numbers"] if n.get("role") != "correction"]
        if displayed != cited:
            raise ValueError("Every monetary amount, including a repeated forecast threshold, needs its own fixture citation")
        citations = []
        for number in story["numbers"]:
            if number["displayed_text"] not in story["text"] and number.get("role") != "correction":
                raise ValueError("Cited number absent from story")
            values, sources = [], []
            for ref in number["sources"]:
                filename = f"companyfacts-CIK{ref['cik']}.json"
                path = ROOT / "tests/fixtures/sec-offline" / filename
                raw = path.read_bytes()
                registered = provenance["snapshots"][filename]
                if digest(raw) != registered["fixture_sha256"]:
                    raise ValueError(f"SEC fixture hash mismatch: {filename}")
                rows = json.loads(raw)["facts"]["us-gaap"][ref["concept"]]["units"]["USD"]
                matches = [(i, row) for i, row in enumerate(rows) if all(row.get(k) == v for k, v in ref["row"].items())]
                if len(matches) != 1:
                    raise ValueError(f"Ambiguous/missing SEC row: {filename}")
                index, row = matches[0]
                values.append(Decimal(row["val"]))
                sources.append({"fixture_path": str(path.relative_to(ROOT)), "fixture_sha256": digest(raw),
                                "original_snapshot_sha256": registered["original_sha256"],
                                "provenance_path": str(provenance_path.relative_to(ROOT)),
                                "provenance_sha256": digest(provenance_raw),
                                "json_pointer": f"/facts/us-gaap/{ref['concept']}/units/USD/{index}", "row": row})
            value = values[0] - sum(values[1:]) if number.get("calculation") == "subtract" else values[0]
            if number.get("scale_error") == 1000:
                stated = Decimal(number["stated_value_usd"])
                if stated != value * 1000:
                    raise ValueError("Unit error must be exactly x1000 of the filed value")
                display = f"${value / Decimal(1_000_000):,.0f} billion"
            else:
                display = f"${(value / Decimal(1_000_000_000)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)} billion"
            if display != number["displayed_text"]:
                raise ValueError(f"Filed value does not produce {number['displayed_text']}")
            citations.append({k: v for k, v in number.items() if k != "sources"} |
                             {"filed_value_usd": int(value), "sources": sources})
        story["fixture_citations"] = citations
    return spec["stories"]


def font(size):
    return ImageFont.truetype(str(EXAMPLES / FONT), size, layout_engine=ImageFont.Layout.BASIC)


def layout(text):
    """One shared layout for the raster post and its native-text PDF."""
    lines, y = [], 72
    for index, paragraph in enumerate(text.strip().split("\n\n")):
        size = 52 if index == 0 else 38
        face = font(size)
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if line and face.getlength(candidate) > SIZE[0] - 144:
                lines.append((line, size, 72, y))
                y += size + 13
                line = word
            else:
                line = candidate
        lines.append((line, size, 72, y))
        y += size + 13 + 20
    if y > SIZE[1] - 34:
        raise ValueError("Story overflows the shared 720p layout")
    return lines


def post_png(text):
    picture = Image.new("RGB", SIZE, "#f7f6f0")
    draw = ImageDraw.Draw(picture)
    draw.line((72, 40, SIZE[0] - 72, 40), fill="#216a50", width=4)
    for line, size, x, y in layout(text):
        draw.text((x, y), line, font=font(size), fill="#18252c", anchor="lt")
    output = BytesIO()
    picture.save(output, format="PNG", optimize=False, compress_level=9)
    return output.getvalue()


def post_pdf(text):
    """A native-text PDF with the very same bundled Noto Serif TC font."""
    meta = json.loads((EXAMPLES / "fonts/metrics.json").read_text())
    font_raw = (EXAMPLES / FONT).read_bytes()
    if digest(font_raw) != meta["font_sha256"]:
        raise ValueError("Font hash mismatch")
    ops = ["0.969 0.965 0.941 rg 0 0 640 360 re f", "0.129 0.416 0.314 RG 2 w 36 340 m 604 340 l S", "0.094 0.145 0.173 rg"]
    for line, size, x, y in layout(text):
        # PDF baseline derived from the actual raster glyph bounds.
        top = font(size).getbbox(line)[1]
        baseline = SIZE[1] / 2 - (y - top + font(size).getmetrics()[0]) / 2
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        ops.append(f"BT /F1 {size / 2:g} Tf {x / 2:g} {baseline:g} Td ({escaped}) Tj ET")
    stream = "\n".join(ops).encode()
    bbox = " ".join(map(str, meta["bbox"]))
    widths = " ".join(map(str, meta["widths"]))
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 640 360] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               f"<< /Type /Font /Subtype /TrueType /BaseFont /NotoSerifTC-Regular /FirstChar 32 /LastChar 126 /Widths [{widths}] /Encoding /WinAnsiEncoding /FontDescriptor 6 0 R >>".encode(),
               f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
               f"<< /Type /FontDescriptor /FontName /NotoSerifTC-Regular /Flags 6 /FontBBox [{bbox}] /ItalicAngle 0 /Ascent {meta['ascent']} /Descent {meta['descent']} /CapHeight 729 /StemV 80 /FontFile2 7 0 R >>".encode(),
               f"<< /Length {len(font_raw)} /Length1 {len(font_raw)} >>\nstream\n".encode() + font_raw + b"\nendstream"]
    raw, offsets = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"), [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(raw))
        raw.extend(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    start = len(raw)
    raw.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    raw.extend(b"".join(f"{offset:010} 00000 n \n".encode() for offset in offsets[1:]))
    raw.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode())
    return bytes(raw)


def probe(path):
    return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)]))


def media_metadata(story):
    path = EXAMPLES / "narration" / f"{story['id']}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    if data["text_sha256"] != digest(story["text"].encode()):
        raise ValueError("Narration belongs to a different story text")
    source = EXAMPLES / data["source_wav"]
    if not source.resolve().is_relative_to(EXAMPLES.resolve()) or digest(source.read_bytes()) != data["source_sha256"]:
        raise ValueError("Retained narration hash mismatch")
    return data


def build(*, check=False):
    if __package__:
        from scripts.run_example_records import check_saved
    else:
        from run_example_records import check_saved
    stories = load_stories()
    font_raw = (EXAMPLES / FONT).read_bytes()
    metrics = json.loads((EXAMPLES / "fonts/metrics.json").read_text())
    if digest(font_raw) != metrics["font_sha256"]:
        raise ValueError("Font hash mismatch")
    manifest = []
    for story in stories:
        stem = story["id"]
        expected = {f"{stem}.txt": story["text"].encode(), f"{stem}.png": post_png(story["text"]),
                    f"{stem}.pdf": post_pdf(story["text"])}
        media = media_metadata(story)
        for kind in ("audio", "video"):
            expected[f"{stem}.{KINDS[kind]}.pending.txt"] = (
                f"PENDING {kind.upper()} for story {stem.upper()}: locked Breeze clone not rendered.\n"
                f"Host: {HOST_COMMAND}\n"
                "This placeholder is not playable media and contains no recorded model result.\n").encode()
        for name, raw in expected.items():
            put(EXAMPLES / name, raw, check)
        for kind, extension in KINDS.items():
            target = f"{stem}.{extension}"
            path = EXAMPLES / target
            details = media.get("outputs", {}).get(kind, {})
            ready = kind not in {"audio", "video"} or bool(details)
            if not ready:
                if path.exists():
                    raise ValueError(f"Media lacks retained provenance: {target}")
                path = EXAMPLES / (target + ".pending.txt")
            raw = path.read_bytes()
            if not 0 < len(raw) <= MAX_BYTES:
                raise ValueError(f"Asset exceeds 2 MB: {path.name}")
            duration = details.get("duration_s")
            if details and (digest(raw) != details["sha256"] or not isinstance(duration, (int, float)) or not 0 < duration <= MAX_SECONDS):
                raise ValueError(f"Media hash/duration mismatch: {target}")
            resolution = list(SIZE) if kind == "image" else details.get("resolution")
            if ready and kind == "video" and (resolution != list(SIZE) or len(raw) != details["size_bytes"]):
                raise ValueError("Video must use the shared 720p layout")
            row = {"id": f"{stem}-{kind}", "story": stem, "story_title": story["title"], "kind": kind,
                             "file": path.name, "target_file": target, "url": "/examples/" + path.name,
                             "status": "ready" if ready else "pending", "sha256": digest(raw), "size_bytes": len(raw),
                             "duration_s": duration, "resolution": resolution, "contains": DESCRIPTIONS[kind],
                             "text_file": f"{stem}.txt", "text_sha256": digest(story["text"].encode()),
                             "font_family": "Noto Serif TC" if kind in {"image", "pdf", "video"} else None,
                             "expected": story["expected"], "fixture_citations": story["fixture_citations"],
                             "saved_result": None, "host_command": HOST_COMMAND if not ready else None}
            row["saved_result"] = check_saved(row, root=ROOT)
            manifest.append(row)
    put(EXAMPLES / "manifest.json", encoded(manifest), check)
    return manifest


def render_media(stories):
    """Same inputs + pinned FFmpeg build/flags produce identical encoded bytes."""
    for story in stories:
        data = media_metadata(story)
        if not data:
            raise ValueError("Synthesize all narration first with --synthesize")
        stem = story["id"]
        source = EXAMPLES / data["source_wav"]
        duration = float(probe(source)["format"]["duration"])
        # Read every word. Speed up a full narration rather than truncating it.
        tempo = max(1, duration / 19.7)
        if tempo > 2:
            raise ValueError("Narration needs >2x speed; retain this attempt and shorten/review the story")
        audio, video = EXAMPLES / f"{stem}.mp3", EXAMPLES / f"{stem}.mp4"
        common = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-fflags", "+bitexact"]
        audio_args = ["-i", str(source), "-map_metadata", "-1", "-af", f"atempo={tempo:.9f}", "-ac", "1", "-ar", "24000",
                      "-c:a", "libmp3lame", "-b:a", "64k", "-flags:a", "+bitexact", "-id3v2_version", "0", str(audio)]
        subprocess.run(common + audio_args, check=True)
        audio_seconds = float(probe(audio)["format"]["duration"])
        video_args = ["-loop", "1", "-framerate", "10", "-i", str(EXAMPLES / f"{stem}.png"), "-i", str(audio),
                      "-map_metadata", "-1", "-c:v", "libx264", "-threads", "1", "-preset", "slow", "-crf", "32",
                      "-tune", "stillimage", "-pix_fmt", "yuv420p", "-flags:v", "+bitexact", "-c:a", "aac", "-b:a", "64k",
                      "-flags:a", "+bitexact", "-shortest", "-t", f"{audio_seconds:.9f}", "-movflags", "+faststart", str(video)]
        subprocess.run(common + video_args, check=True)
        outputs = {}
        for kind, path in (("audio", audio), ("video", video)):
            info = probe(path)
            seconds = float(info["format"]["duration"])
            if not 0 < seconds <= MAX_SECONDS or not 0 < path.stat().st_size <= MAX_BYTES:
                raise ValueError("Retain the attempt; media exceeds 20 seconds or 2 MB")
            visual = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
            outputs[kind] = {"sha256": digest(path.read_bytes()), "size_bytes": path.stat().st_size, "duration_s": seconds,
                             "resolution": [visual["width"], visual["height"]] if visual else None}
        data.update(outputs=outputs, atempo=round(tempo, 9), ffmpeg_version=subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[0])
        put(EXAMPLES / "narration" / f"{stem}.json", encoded(data))


def synthesize(video_repo, breeze, device="mps"):
    """Host only. Freeze the locked clone and every attempt; no substitute voice."""
    stories = load_stories()
    reference = video_repo / "demo/assets/voice/narrator-ref.wav"
    if digest(reference.read_bytes()) != REF_SHA256:
        raise ValueError("Locked narrator reference hash mismatch")
    if any((EXAMPLES / "narration" / f"{s['id']}.json").exists() for s in stories):
        raise ValueError("Narration already selected; retain it and use --render-media to rebuild")
    record = EXAMPLES / "production" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    record.mkdir(parents=True, exist_ok=False)
    jobs = [{"id": s["id"], "text": " ".join(s["text"].split()), "out": str(record / f"{s['id']}.wav")} for s in stories]
    put(record / "jobs.json", encoded(jobs))
    pins = json.loads((breeze / "pins.json").read_text())
    if pins != {"model_id": "BreezeBlue/Breeze-TTS-2", "model_revision": "3e28c5151381a722f1d8661b4118c298caa77aa4",
                "code_url": "https://github.com/breezeblue-ai/breeze-tts.git", "code_commit": "6eba901d1845353802652c708a4740fdfc5baa75"}:
        raise ValueError("Breeze code/model pins differ from the locked narrator pipeline")
    plan = {"engine": "breeze-tts-2", "mode": "clone", "seed": 2026, "ref_audio_sha256": REF_SHA256,
            "ref_text": REF_TEXT, "pins": pins, "device": device, "host_command": HOST_COMMAND,
            "text_sha256": {s["id"]: digest(s["text"].encode()) for s in stories}, "attempts": 1}
    put(record / "inputs.json", encoded(plan))
    with (record / "synthesis.log").open("w") as log:
        status = subprocess.run([str(breeze / "run.sh"), "--device", device, "--jobs", str(record / "jobs.json"),
                                 "--ref-audio", str(reference), "--ref-text", REF_TEXT, "--seed", "2026"],
                                stdout=log, stderr=subprocess.STDOUT).returncode
    put(record / "receipt.json", encoded({"exit_code": status, "finished_at": datetime.now(timezone.utc).isoformat()}))
    if status:
        raise ValueError(f"Breeze failed; retained attempt at {record.relative_to(ROOT)}")
    for s in stories:
        wav = record / f"{s['id']}.wav"
        put(EXAMPLES / "narration" / f"{s['id']}.json", encoded({"text_sha256": digest(s["text"].encode()),
            "source_wav": str(wav.relative_to(EXAMPLES)), "source_sha256": digest(wav.read_bytes()),
            "production_plan": str((record / "inputs.json").relative_to(EXAMPLES)), "outputs": {}}))
    render_media(stories)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--synthesize", action="store_true", help="HOST ONLY: calls the locked Breeze clone")
    parser.add_argument("--render-media", action="store_true", help="HOST ONLY: rebuild MP3/MP4 from retained WAVs")
    parser.add_argument("--video-repo", type=Path, default=Path("/Users/yan/git/market-claim-verifier-video"))
    parser.add_argument("--breeze", type=Path, default=Path("/Users/yan/ml-engines/breeze-tts"))
    parser.add_argument("--device", choices=("mps", "cpu"), default="mps")
    args = parser.parse_args()
    if args.check and (args.synthesize or args.render_media):
        parser.error("--check never synthesizes or probes media")
    if args.synthesize and args.render_media:
        parser.error("Choose --synthesize or --render-media")
    if args.synthesize or args.render_media:
        build()
        if args.synthesize:
            synthesize(args.video_repo, args.breeze, args.device)
        else:
            render_media(load_stories())
    rows = build(check=args.check)
    print(f"{'Checked' if args.check else 'Built'} {len(rows)} examples: {sum(r['status'] == 'ready' for r in rows)} ready")


if __name__ == "__main__":
    main()
