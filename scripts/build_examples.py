#!/usr/bin/env python3
"""Build the self-made example files/manifest without network or model calls.

Only --synthesize invokes the host's locked Breeze voice. Verification never
uses that flag. Missing narration/video are explicit .pending.txt assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs/site/examples"
KINDS = {"text": "txt", "image": "png", "pdf": "pdf", "audio": "mp3", "video": "mp4"}
CONTAINS = {
    "text": {"en": "The saved Big Tech post, including the wrong Apple quarter.", "zh": "已保存的科技股貼文，含 Apple 季度數字錯誤。"},
    "image": {"en": "The same post as a screenshot. Muse reads the visible text.", "zh": "同一篇貼文的截圖，由 Muse 讀取畫面文字。"},
    "pdf": {"en": "A one-page post with native text, read without OCR.", "zh": "單頁原生文字 PDF，直接讀取文字，不經 OCR。"},
    "audio": {"en": "The post read by the locked Breeze narrator. Muse transcribes it.", "zh": "由鎖定的 Breeze 旁白朗讀貼文，再由 Muse 轉錄。"},
    "video": {"en": "The screenshot with narration. Muse reads three frames and the audio.", "zh": "截圖搭配旁白；Muse 讀取三個影格並轉錄音軌。"},
}
REF_TEXT = ("This is Market Claim Verifier. Paste a finance post, and every number is checked against the company's "
            "own SEC filings, with a link to the exact line that proves it.")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def post_pdf(text):
    """Deterministic, native-text Times PDF (the site's document serif family).

    A ToUnicode map preserves the thread emoji in extracted text. Its visible
    mark is drawn as a small spool, avoiding system-font/emoji dependencies.
    """
    operations = ["0.969 0.965 0.941 rg 0 0 595 842 re f", "0.094 0.145 0.173 rg"]
    y = 755
    for i, paragraph in enumerate(text.strip().split("\n\n")):
        size = 25 if i == 0 else 18
        for line in textwrap.wrap(paragraph, width=45 if i == 0 else 57, break_long_words=False, break_on_hyphens=False):
            encoded = line.replace("🧵", "€").encode("cp1252")
            escaped = encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
            operations.append(f"BT /F1 {size} Tf 48 {y} Td (" + escaped.decode("latin1") + ") Tj ET")
            if "🧵" in line:
                operations.append(f"0.137 0.420 0.314 rg 340 {y - 1} 12 3 re f 343 {y + 2} 6 11 re f 340 {y + 13} 12 3 re f 0.094 0.145 0.173 rg")
            y -= 29
        y -= 20
    stream = "\n".join(operations).encode("latin1")
    mapping = "\n".join(f"<{i:02X}> <{('🧵' if i == 128 else bytes([i]).decode('cp1252')).encode('utf-16-be').hex().upper()}>"
                        for i in range(32, 256) if i not in {129, 141, 143, 144, 157})
    mapped = mapping.splitlines()
    cmap = ("/CIDInit /ProcSet findresource begin 12 dict begin begincmap\n"
            "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
            "/CMapName /PostText def /CMapType 2 def\n1 begincodespacerange <00> <FF> endcodespacerange\n"
            + "".join(f"{len(mapped[i:i + 100])} beginbfchar\n" + "\n".join(mapped[i:i + 100]) + "\nendbfchar\n"
                      for i in range(0, len(mapped), 100)) +
            "endcmap CMapName currentdict /CMap defineresource pop end end").encode()
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding << /Type /Encoding /BaseEncoding /WinAnsiEncoding /Differences [128 /space] >> /ToUnicode 6 0 R >>",
               f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
               f"<< /Length {len(cmap)} >>\nstream\n".encode() + cmap + b"\nendstream"]
    raw, offsets = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"), [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(raw))
        raw.extend(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    start = len(raw)
    raw.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    raw.extend("".join(f"{offset:010} 00000 n \n" for offset in offsets[1:]).encode())
    raw.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode())
    return bytes(raw)


def synthesize(video_repo, breeze):
    """Host only. No substitute voice; preserve all receipts and failed logs."""
    from datetime import datetime, timezone
    record = ROOT / "docs/evidence/example-assets" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    record.mkdir(parents=True, exist_ok=False)
    reference = video_repo / "demo/assets/voice/narrator-ref.wav"
    if not reference.is_file():
        raise SystemExit("Locked narrator reference missing: " + str(reference))
    text = (EXAMPLES / "post.txt").read_text()
    jobs = [{"id": "example-post", "text": " ".join(text.split()), "out": str(record / "source.wav")}]
    (record / "jobs.json").write_text(json.dumps(jobs, indent=2) + "\n")
    (record / "inputs.json").write_text(json.dumps({"post_sha256": digest(text.encode()),
        "reference_sha256": digest(reference.read_bytes()), "ref_text": REF_TEXT, "seed": 2026,
        "engine": "breeze-tts-2", "reference_source": "demo/storyboard-v4.yaml"}, indent=2) + "\n")
    with (record / "synthesis.log").open("w") as log:
        subprocess.run([str(breeze / "run.sh"), "--device", "auto", "--jobs", str(record / "jobs.json"),
                        "--ref-audio", str(reference), "--ref-text", REF_TEXT, "--seed", "2026"],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(record / "source.wav"),
                    "-map_metadata", "-1", "-ac", "1", "-ar", "24000", "-c:a", "libmp3lame", "-b:a", "64k",
                    str(EXAMPLES / "post.mp3")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-loop", "1", "-i", str(EXAMPLES / "post.png"),
                    "-i", str(EXAMPLES / "post.mp3"), "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf7f6f0,setsar=1",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "32", "-tune", "stillimage", "-r", "10",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k", "-shortest", "-movflags", "+faststart",
                    "-map_metadata", "-1", str(EXAMPLES / "post.mp4")], check=True)
    if (EXAMPLES / "post.mp4").stat().st_size > 2_000_000:
        raise SystemExit("Video exceeds 2 MB; retain the attempt and lower the encode bitrate before publishing")


def build(*, check=False, refresh_media=False):
    post = json.loads((ROOT / "docs/site/data/live-demo-post.json").read_text())["input"]
    expected = {"post.txt": post.encode(), "post.pdf": post_pdf(post)}
    prior = json.loads((EXAMPLES / "manifest.json").read_text()) if (EXAMPLES / "manifest.json").exists() else []
    for kind in ("audio", "video"):
        filename = f"post.{KINDS[kind]}.pending.txt"
        expected[filename] = (f"PENDING {kind.upper()}: locked Breeze narration has not been synthesized.\n"
            "Host: python3 scripts/build_examples.py --synthesize --video-repo /Users/yan/git/market-claim-verifier-video\n"
            "This is a placeholder, not playable media or a recorded model result.\n").encode()
    if not check:
        EXAMPLES.mkdir(parents=True, exist_ok=True)
    for name, raw in expected.items():
        path = EXAMPLES / name
        if check:
            if not path.exists() or path.read_bytes() != raw:
                raise ValueError(f"Stale example: {name}")
        else:
            path.write_bytes(raw)
    manifest = []
    for kind, extension in KINDS.items():
        target = f"post.{extension}"
        path = EXAMPLES / target
        ready = path.is_file()
        if not ready and kind not in {"audio", "video"}:
            raise ValueError(f"Required example missing: {target}")
        if not ready:
            path = EXAMPLES / (target + ".pending.txt")
        duration = None
        if ready and kind in {"audio", "video"}:
            previous = next((r for r in prior if r["id"] == kind and r["sha256"] == digest(path.read_bytes())), {})
            duration = previous.get("duration_s")
            if refresh_media:
                duration = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)]))
            if not duration or duration > 60:
                raise ValueError("Ready media needs a measured duration <=60 s; use --refresh-media")
        if ready and kind == "video" and path.stat().st_size > 2_000_000:
            raise ValueError("Video exceeds 2 MB")
        manifest.append({"id": kind, "kind": kind, "file": path.name, "target_file": target,
                         "status": "ready" if ready else "pending", "sha256": digest(path.read_bytes()),
                         "size_bytes": path.stat().st_size, "duration_s": duration,
                         "contains": CONTAINS[kind]})
    raw = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if check:
        if (EXAMPLES / "manifest.json").read_text() != raw:
            raise ValueError("Stale examples manifest")
    else:
        (EXAMPLES / "manifest.json").write_text(raw)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--refresh-media", action="store_true")
    parser.add_argument("--synthesize", action="store_true", help="HOST ONLY: invokes local Breeze")
    parser.add_argument("--video-repo", type=Path, default=Path("/Users/yan/git/market-claim-verifier-video"))
    parser.add_argument("--breeze", type=Path, default=Path("/Users/yan/ml-engines/breeze-tts"))
    args = parser.parse_args()
    if args.check and (args.synthesize or args.refresh_media):
        parser.error("--check never synthesizes or probes media")
    if args.synthesize:
        build()
        synthesize(args.video_repo, args.breeze)
    build(check=args.check, refresh_media=args.refresh_media or args.synthesize)


if __name__ == "__main__":
    main()
