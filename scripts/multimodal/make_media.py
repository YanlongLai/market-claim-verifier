"""Make the small probe fixtures locally: Pillow, macOS say, ffmpeg; no model calls.

Run from any directory with this repository's Python environment. --visuals-only
does not use the speech service. Audio generation fails if say produces silence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import textwrap
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests/fixtures/multimodal"
POST = (
    "Example post\nFictional author: Example Investor\n\n"
    "Apple reported revenue of $94.036 billion for fiscal Q3 2025.\n"
    "Apple reported diluted EPS of $1.67 for fiscal Q3 2025.\n\n"
    "Self-made test: one number is deliberately wrong."
)
NARRATION = (
    "Example recording. A synthetic narrator is reading Apple's fiscal 2025 third quarter release. "
    "This is not an executive recording. "
    "Apple today announced financial results for its fiscal 2025 third quarter ended June 28, 2025. "
    "The Company posted quarterly revenue of 94.0 billion dollars, up 10 percent year over year, "
    "and quarterly diluted earnings per share of 1.67 dollars, up 12 percent year over year. "
    "We are very pleased with our record business performance for the June quarter, "
    "which generated EPS growth of 12 percent, said Kevan Parekh, Apple's CFO. "
    "End of example recording."
)


def run(*args: str) -> None:
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def card(path: Path, title: str, lines: list[str]) -> None:
    im = Image.new("RGB", (1000, 620), "#f5f3ed")
    draw = ImageDraw.Draw(im)
    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    font = ImageFont.truetype(font_path, 29)
    small = ImageFont.truetype(font_path, 20)
    heading = ImageFont.truetype(font_path, 40)
    draw.text((54, 44), title, font=heading, fill="#173846")
    y = 132
    for line in lines:
        for row in textwrap.wrap(line, 53) or [""]:
            draw.text((54, y), row, font=font, fill="#182128")
            y += 45
    draw.text((54, 570), "Self-made probe fixture | No real speaker audio", font=small, fill="#53636a")
    im.save(path, optimize=True)


def captioned_video() -> None:
    """A separate control: table values expressed as complete dated sentences."""
    card(OUT / "captioned-1.png", "Apple | fiscal Q3 2025", [
        "Apple reported total net sales of $94,036 million for fiscal Q3 2025.",
        "Apple reported net income of $23,434 million for fiscal Q3 2025.",
        "Selected values from the SEC 8-K Ex 99.1 table.",
    ])
    card(OUT / "captioned-2.png", "Apple | fiscal Q3 2025", [
        "Apple reported diluted EPS of $1.57 for fiscal Q3 2025.",
        "Selected value from the SEC 8-K Ex 99.1 table.",
    ])
    card(OUT / "captioned-3.png", "Example | deliberately wrong", [
        "Apple reported diluted EPS of $1.67 for fiscal Q3 2025.",
        "Compare this number with the filed release table.",
    ])
    with wave.open(str(OUT / "release-reading.wav")) as wav:
        duration = wav.getnframes() / wav.getframerate()
    with tempfile.TemporaryDirectory(prefix="claimcheck-captioned-") as tmp:
        concat = Path(tmp) / "slides.txt"
        concat.write_text("".join(f"file '{OUT / f'captioned-{i}.png'}'\nduration {duration / 3:.6f}\n" for i in (1, 2, 3)) + f"file '{OUT / 'captioned-3.png'}'\n")
        run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
            "-i", str(OUT / "release-reading.wav"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-r", "5",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "48k", "-t", str(duration),
            "-movflags", "+faststart", str(OUT / "release-captioned.mp4"))
    manifest = json.loads((OUT / "manifest.json").read_text())
    manifest["captioned_control"] = "Same audio and selected table values; each claim now has an explicit issuer/fiscal period. Created after inspecting row-only video failures."
    for path in [*OUT.glob("captioned-*.png"), OUT / "release-captioned.mp4"]:
        manifest["files"][path.name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visuals-only", action="store_true")
    parser.add_argument("--espeak-bin", type=Path, help="explicit offline formant-synthesis fallback if macOS say is unavailable")
    parser.add_argument("--variants", action="store_true", help="also make smaller OCR, number-word text, two-voice audio and silent video controls")
    parser.add_argument("--captioned-only", action="store_true", help="make a separate sentence-captioned video control from existing audio")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.captioned_only:
        captioned_video()
        return
    (OUT / "post.txt").write_text(POST + "\n")
    (OUT / "narration.txt").write_text(NARRATION + "\n")
    card(OUT / "example-post.png", "Example post", POST.splitlines()[1:])
    card(OUT / "slide-1.png", "Apple | fiscal Q3 2025", [
        "Release table: three months ended June 28, 2025",
        "Total net sales: $94,036 million",
        "Net income: $23,434 million",
        "SEC 8-K Ex 99.1 | filed July 31, 2025",
    ])
    card(OUT / "slide-2.png", "Apple | fiscal Q3 2025", [
        "Release table: three months ended June 28, 2025",
        "Diluted earnings per share: $1.57",
        "SEC 8-K Ex 99.1 | filed July 31, 2025",
    ])
    card(OUT / "slide-3.png", "Apple | fiscal Q3 2025", [
        "Example slide: deliberately wrong number",
        "Diluted earnings per share: $1.67",
        "Compare with the filed release table.",
    ])
    if not args.visuals_only:
        with tempfile.TemporaryDirectory(prefix="claimcheck-media-") as tmp:
            aiff = str(Path(tmp) / "narration.aiff")
            if args.espeak_bin:
                aiff = str(Path(tmp) / "narration.wav")
                run(str(args.espeak_bin), "-v", "en-us", "-s", "150", "-f", str(OUT / "narration.txt"), "-w", aiff)
            else:
                run("say", "-v", "Samantha", "-r", "150", "-f", str(OUT / "narration.txt"), "-o", aiff)
            wav = OUT / "release-reading.wav"
            run("ffmpeg", "-v", "error", "-y", "-i", aiff, "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(wav))
            with wave.open(str(wav)) as audio:
                duration = audio.getnframes() / audio.getframerate()
            if not 30 <= duration <= 60:
                raise RuntimeError(f"synthesizer generated {duration:.3f}s; expected 30–60s of audible narration")
            concat = Path(tmp) / "slides.txt"
            concat.write_text("".join(f"file '{OUT / f'slide-{i}.png'}'\nduration {duration / 3:.6f}\n" for i in (1, 2, 3)) + f"file '{OUT / 'slide-3.png'}'\n")
            run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-r", "5",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "48k", "-t", str(duration),
                "-movflags", "+faststart", str(OUT / "release-slides.mp4"))
            if args.variants:
                # Distinct formant voices, not cloned people. The second turn is
                # deliberately wrong, just like the main sample's EPS number.
                dialogue = [
                    "Example recording with two synthetic voices. This is not an executive call. "
                    "Apple reported revenue of ninety four point zero three six billion dollars for fiscal two thousand twenty five third quarter.",
                    "Example second voice. Apple reported diluted earnings per share of one point six seven dollars for fiscal two thousand twenty five third quarter. End of example recording.",
                ]
                clips = []
                for i, text in enumerate(dialogue):
                    (OUT / f"dialogue-{i + 1}.txt").write_text(text + "\n")
                    dest = str(Path(tmp) / f"voice-{i}.wav")
                    if args.espeak_bin:
                        run(str(args.espeak_bin), "-v", ("en-us", "en-us+f3")[i], "-s", "150", "-f", str(OUT / f"dialogue-{i + 1}.txt"), "-w", dest)
                    else:
                        run("say", "-v", ("Samantha", "Fred")[i], "-r", "150", "-f", str(OUT / f"dialogue-{i + 1}.txt"), "-o", dest, "--file-format=WAVE", "--data-format=LEI16@24000")
                    clips.append(dest)
                run("ffmpeg", "-v", "error", "-y", "-i", clips[0], "-i", clips[1], "-filter_complex",
                    "[0:a][1:a]concat=n=2:v=0:a=1[out]", "-map", "[out]", "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", str(OUT / "two-voices.wav"))
                run("ffmpeg", "-v", "error", "-y", "-i", str(OUT / "release-slides.mp4"), "-an", "-c:v", "copy", str(OUT / "slides-silent.mp4"))
    if args.variants:
        with Image.open(OUT / "example-post.png") as image:
            image.resize((500, 310)).save(OUT / "example-post-small.png", optimize=True)
        (OUT / "post-words.txt").write_text(
            "Example post. Apple fiscal two thousand twenty five third quarter.\n"
            "Apple reported revenue of ninety four point zero three six billion dollars for fiscal two thousand twenty five third quarter.\n"
            "Apple reported diluted EPS of one point six seven dollars for fiscal two thousand twenty five third quarter.\n")
    files = [p for p in sorted(OUT.iterdir()) if p.suffix in {".txt", ".png", ".wav", ".mp4"}]
    previous = json.loads((OUT / "manifest.json").read_text()) if (OUT / "manifest.json").exists() else {}
    manifest = {
        **previous,
        "source_fixture": "tests/fixtures/releases/manifest.json (AAPL)",
        "source_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000071/a8-kex991q3202506282025.htm",
        "source_sha256": "d5346aba9205cb8e56d89a380ebb53e9b25863d528b0baed5a6e3b087ee219fb",
        "generation": ("Pillow; eSpeak NG 1.53.0 offline formant synthesis at 150 wpm; ffmpeg. "
                       "Fallback: macOS say returned sandbox_extension_issue_file and zero audio frames with Samantha and Fred. "
                       "No generative model used for test media; no real call audio downloaded."
                       if args.espeak_bin else "Pillow; macOS say Samantha at 150 wpm; ffmpeg; no generative model"),
        "audio_generated": (OUT / "release-reading.wav").is_file(),
        "disclosure": "Synthetic narrator; not Kevan Parekh's voice. Release wording is excerpted, spoken notation expanded; EPS deliberately changed from 1.57 to 1.67. Slides 1–2 reproduce selected table values; slide 3 has the same deliberate EPS error.",
        "expected_post_numbers": ["94.036 billion", "1.67"],
        "expected_audio_financial_numbers": ["94.0 billion", "10 percent", "1.67", "12 percent", "12 percent"],
        "expected_frame_financial_numbers": {"slide-1.png": ["94,036 million", "23,434 million"], "slide-2.png": ["1.57"], "slide-3.png": ["1.67"]},
        "expected_two_voice_numbers": ["94.036 billion", "1.67"],
        "files": {p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size} for p in files},
    }
    if args.visuals_only:
        manifest["generation"] = previous.get("generation", "Pillow visuals only; no audio generated")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(files)} self-made assets to {OUT}")


if __name__ == "__main__":
    main()
