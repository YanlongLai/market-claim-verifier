"""Local media operations. No network, downloaded fonts, or ffmpeg text filters."""
from __future__ import annotations

import json
import math
import re
import subprocess
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pipeline import BuildError, Timing, subtitle_timing

FFMPEG = Path("/opt/homebrew/bin/ffmpeg")
FFPROBE = Path("/opt/homebrew/bin/ffprobe")
SIZE = (1920, 1080)
FPS = 30
CROSSFADE = 0.4
MIN_INTEGRATED_S = 10.0


def command(args: list, log: Path | None = None) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run([str(a) for a in args], text=True, capture_output=True, check=False)
    except OSError as error:
        raise BuildError(f"Cannot run {args[0]}: {error}") from error
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(result.stdout + result.stderr)
    if result.returncode:
        raise BuildError(f"{Path(str(args[0])).name} exited {result.returncode}:\n"
                         f"{(result.stderr or result.stdout)[-2400:]}"
                         + (f"\nFull log: {log}" if log else ""))
    return result


def ffmpeg(args: list, log: Path | None = None, *, verbose: bool = False) -> subprocess.CompletedProcess:
    return command([FFMPEG, "-hide_banner", "-nostdin", "-y", "-loglevel", "info" if verbose else "warning",
                    "-filter_threads", "1", "-filter_complex_threads", "1", *args], log)


def probe(path: Path) -> dict:
    result = command([FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    return json.loads(result.stdout)


def duration(path: Path) -> float:
    info = probe(path)
    values = [info.get("format", {}).get("duration"), *[s.get("duration") for s in info.get("streams", [])]]
    seconds = max((float(v) for v in values if v is not None and v != "N/A"), default=0)
    if not math.isfinite(seconds) or seconds <= 0:
        raise BuildError(f"{path}: zero-length or invalid audio/video. macOS say can return an empty file in the "
                         "sandbox; synthesize on the host. No silent substitute was created.")
    return seconds


def normalize_voice(source: Path, destination: Path) -> float:
    duration(source)
    ffmpeg(["-i", source, "-vn", "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", destination],
           destination.parent / "normalize.log")
    return duration(destination)


def video_encoder() -> list[str]:
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-threads", "2"]


def normalize_capture(source: Path, webm: Path, mp4: Path, seconds: float, lead_s: float) -> None:
    if duration(source) + 0.15 < lead_s + seconds:
        raise BuildError(f"Capture ended early: {source}. Re-record on the host; missing action footage is not fabricated.")
    filters = f"fps={FPS},scale=1920:1080:flags=lanczos,setsar=1,trim=duration={seconds:.9f},setpts=PTS-STARTPTS"
    ffmpeg(["-ss", f"{lead_s:.9f}", "-i", source, "-an", "-vf", filters, "-t", f"{seconds:.9f}",
            "-c:v", "libvpx-vp9", "-deadline", "realtime", "-cpu-used", "8", "-b:v", "4M", "-threads", "2", webm],
           webm.parent / "webm.log")
    ffmpeg(["-i", webm, "-an", "-vf", f"fps={FPS},setsar=1", "-t", f"{seconds:.9f}",
            *video_encoder(), "-movflags", "+faststart", mp4], mp4.parent / "normalize.log")


def font_path() -> Path:
    for candidate in ("/Library/Fonts/Arial Unicode.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
                      "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/System/Library/Fonts/PingFang.ttc",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        path = Path(candidate)
        if path.exists():
            return path
    raise BuildError("No suitable system font. Install Arial Unicode or set up a system font before assembling.")


def text_panel(text: str, destination: Path, *, lower_third: bool = False, font_size: int | None = None) -> None:
    """Transparent, tightly cropped typography for the top label and bottom subtitles."""
    font = ImageFont.truetype(str(font_path()), font_size if font_size is not None else (42 if lower_third else 50))
    measure = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = text.splitlines()
    widths = [measure.textlength(line, font=font) for line in lines]
    # Two subtitle lines must fit 880–1016 px (bottom 200 px zone, 64 px safe margin): 2·60 + 16 = 136.
    line_height = 59 if lower_third else 60
    width = math.ceil(max(widths, default=0)) + 64
    pad = 24 if lower_third else 16
    height = len(lines) * line_height + pad
    if width > 1728:
        raise BuildError(f"Caption exceeds the 1080p safe area: {text}")
    panel = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(panel)
    draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=12, fill=(17, 26, 32, 238))
    if lower_third:
        draw.rounded_rectangle((0, 0, 5, height - 1), radius=2, fill=(61, 220, 151, 255))
    for line, line_width, index in zip(lines, widths, range(len(lines))):
        x = 32 if lower_third else (width - line_width) / 2
        y = pad // 2 + index * line_height
        if font_size is not None and font_size >= 56:
            # Arial Unicode's ascender offset otherwise clips 56 px descenders.
            # Center actual glyphs inside the existing 60 px caption line box.
            bounds = font.getbbox(line)
            y += (line_height - (bounds[3] - bounds[1])) / 2
            draw.text((x, y), line, fill="white", font=font, stroke_width=0, anchor="lt")
        else:
            draw.text((x, y), line, fill="white", font=font, stroke_width=0)
    panel.save(destination)


def render_scene(visual: Path, kind: str, scene: dict, timing: Timing, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    frames = round(timing.final_s * FPS)
    args = []
    if kind in ("image", "card"):
        args += ["-loop", "1", "-framerate", str(FPS)]
    args += ["-i", visual]
    lower = destination.parent / "lower-third.png"
    text_panel(scene["on_screen"], lower, lower_third=True)
    args += ["-loop", "1", "-framerate", str(FPS), "-i", lower]
    cues = subtitle_timing(scene["narration"], timing.voice_s)
    for i, cue in enumerate(cues):
        panel = destination.parent / f"subtitle-{i:03}.png"
        text_panel(cue.text, panel)
        args += ["-loop", "1", "-framerate", str(FPS), "-i", panel]
    filters = []
    if kind in ("image", "card"):
        filters.append(f"[0:v]scale=3840:2160:flags=lanczos,zoompan="
                       f"z='1+0.06*min(on/{max(1, frames - 1)},1)':"
                       "x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
                       f"d=1:s=1920x1080:fps={FPS},setsar=1[base]")
    else:
        filters.append(f"[0:v]fps={FPS},scale=1920:1080:force_original_aspect_ratio=decrease,"
                       f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,"
                       f"tpad=stop_mode=clone:stop_duration={timing.final_s:.9f},"
                       f"trim=duration={timing.final_s:.9f},setpts=PTS-STARTPTS[base]")
    fade_in = min(0.25, timing.final_s / 8)
    fade_out = max(fade_in, timing.final_s - 0.65)
    filters += [f"[1:v]format=rgba,fade=t=in:st=0:d={fade_in:.9f}:alpha=1,"
                f"fade=t=out:st={fade_out:.9f}:d={fade_in:.9f}:alpha=1[lt]",
                "[base][lt]overlay=x=64:y=64:shortest=1[b0]"]
    for i, cue in enumerate(cues):
        filters.append(f"[b{i}][{i+2}:v]overlay=x=(W-w)/2:y=H-h-66:shortest=1:"
                       f"enable='gte(t,{cue.start:.9f})*lt(t,{cue.end:.9f})'[b{i+1}]")
    args += ["-filter_complex", ";".join(filters), "-map", f"[b{len(cues)}]", "-an", "-frames:v", str(frames),
             *video_encoder(), "-movflags", "+faststart", destination]
    ffmpeg(args, destination.parent / "render.log")


def join_visuals(clips: list[Path], timings: list[Timing], destination: Path) -> None:
    args = []
    filters = []
    for i, clip in enumerate(clips):
        args += ["-i", clip]
        filters.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
    current = "v0"
    for i, timing in enumerate(timings[1:], 1):
        following = f"x{i}"
        filters.append(f"[{current}][v{i}]xfade=transition=fade:duration={CROSSFADE}:"
                       f"offset={timing.start_s:.9f}[{following}]")
        current = following
    total = timings[-1].start_s + timings[-1].final_s
    args += ["-filter_complex", ";".join(filters), "-map", f"[{current}]", "-an", "-t", f"{total:.9f}",
             *video_encoder(), "-movflags", "+faststart", destination]
    ffmpeg(args, destination.parent / "join.log")


def mix_audio(voices: list[Path], timings: list[Timing], music: Path | None, gain_db: float, destination: Path) -> None:
    args = []
    filters = []
    for i, (voice, timing) in enumerate(zip(voices, timings)):
        args += ["-i", voice]
        # Transitions consume silence, never the end of a spoken sentence.
        length = timing.final_s - (CROSSFADE if i < len(timings)-1 else 0)
        filters.append(f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                       f"apad,atrim=duration={length:.9f},asetpts=PTS-STARTPTS[a{i}]")
    filters.append("".join(f"[a{i}]" for i in range(len(voices))) + f"concat=n={len(voices)}:v=0:a=1[voice]")
    total = timings[-1].start_s + timings[-1].final_s
    output = "voice"
    if music:
        index = len(voices)
        args += ["-stream_loop", "-1", "-i", music]
        filters += ["[voice]asplit=2[narration][sidechain]",
                    f"[{index}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                    f"volume={gain_db}dB,atrim=duration={total:.9f},asetpts=PTS-STARTPTS,"
                    f"afade=t=out:st={max(0, total-2):.9f}:d={min(2, total):.9f}[bed]",
                    "[bed][sidechain]sidechaincompress=threshold=0.025:ratio=6:attack=30:release=400[ducked]",
                    "[narration][ducked]amix=inputs=2:duration=first:normalize=0[mixed]"]
        output = "mixed"
    args += ["-filter_complex", ";".join(filters), "-map", f"[{output}]", "-t", f"{total:.9f}",
             "-c:a", "pcm_s24le", "-ar", "48000", "-ac", "2", destination]
    ffmpeg(args, destination.parent / "mix.log")


def loudness(path: Path, log: Path, target_tp: float = -1.5, target_i: float = -14) -> dict:
    result = ffmpeg(["-i", path, "-vn", "-af", f"loudnorm=I={target_i}:TP={target_tp}:LRA=11:print_format=json",
                     "-f", "null", "-"], log, verbose=True)
    matches = re.findall(r'\{\s*"input_i".*?\}', result.stderr, flags=re.S)
    if not matches:
        raise BuildError(f"ffmpeg did not return loudnorm measurements. See {log}")
    data = json.loads(matches[-1])
    if not all(math.isfinite(float(data[k])) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")):
        raise BuildError("Narration is silent or loudness cannot be measured; no export was produced.")
    return data


def loudness_report(path: Path, log: Path) -> dict:
    """Read-only EBU R128 scan, including the 400 ms and 3 s loudness windows.

    Missing windows (or silence) are null, rather than the scanner's -120 LUFS
    warm-up value. Integrated loudness here is information, never a clip gate.
    """
    result = ffmpeg(["-i", path, "-vn", "-af", "ebur128=peak=true:metadata=1,ametadata=print",
                     "-f", "null", "-"], log, verbose=True)
    def maximum(name: str) -> float | None:
        values = [float(v) for v in re.findall(rf"lavfi\.r128\.{name}=([-+\d.e]+)", result.stderr)]
        return max((v for v in values if math.isfinite(v) and v > -120), default=None)
    integrated = re.findall(r"\bI:\s*([-+\d.inf]+) LUFS", result.stderr)
    peaks = re.findall(r"Peak:\s*([-+\d.inf]+) dBFS", result.stderr)
    if not integrated or not peaks:
        raise BuildError(f"ffmpeg did not return EBU R128 measurements. See {log}")
    level, peak = float(integrated[-1]), float(peaks[-1])
    return {"measured_lufs": level if math.isfinite(level) and level > -70 else None,
            "momentary_max_lufs": maximum("M"), "short_term_max_lufs": maximum("S"),
            "true_peak_dbtp": peak if math.isfinite(peak) else None,
            "momentary_window_s": 0.4, "short_term_window_s": 3.0}


def delivery_ok(measured: dict) -> bool:
    integrated, peak = float(measured["input_i"]), float(measured["input_tp"])
    return math.isfinite(integrated) and math.isfinite(peak) and peak <= -1 and abs(integrated + 14) <= 1


def prepare_audio_master(audio: Path, destination: Path, total_s: float) -> dict:
    """Normalize the entire mix once; retain lossless PCM and verified delivery AAC.

    Excerpts must be cut AFTER this stage: both the ducking envelope and loudnorm
    (which can fall back to dynamic mode) depend on the preceding full timeline.
    """
    if total_s < MIN_INTEGRATED_S:
        raise BuildError("Integrated normalization needs the full mix (at least 10 s), not an excerpt.")
    target_tp = -1.5
    target_i = -14.0
    encoded = destination.with_suffix('.m4a')
    for attempt in range(3):
        measured = loudness(audio, destination.parent / f"loudness-pass1-{attempt}.log", target_tp, target_i)
        normalizer = (f"loudnorm=I={target_i}:TP={target_tp}:LRA=11:"
                      f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
                      f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
                      f"offset={measured['target_offset']}:linear=true:print_format=json")
        ffmpeg(["-i", audio, "-vn", "-af", normalizer + ",apad", "-t", f"{total_s:.9f}",
                "-c:a", "pcm_s24le", "-ar", "48000", "-ac", "2", destination],
               destination.parent / f"loudness-pass2-{attempt}.log", verbose=True)
        ffmpeg(["-i", destination, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-t", f"{total_s:.9f}", "-movflags", "+faststart", encoded],
               destination.parent / f"loudness-aac-{attempt}.log")
        verified = loudness(encoded, destination.parent / f"loudness-verify-{attempt}.log")
        peak = float(verified["input_tp"])
        integrated = float(verified["input_i"])
        if delivery_ok(verified):
            return {"target_lufs": -14, "measured_lufs": integrated, "true_peak_dbtp": peak,
                    "two_pass": True, "pass1": measured, "verification": verified,
                    "integrated_gate": True, "reference_duration_s": total_s,
                    "normalizer": normalizer, "attempts": attempt + 1}
        # Correct loudness separately from AAC peak overshoot; lowering the peak
        # ceiling alone cannot repair an under-target integrated level.
        target_i = min(-5, max(-70, target_i - 14 - integrated))
        if peak > -1:
            target_tp = max(-9, target_tp - max(0.25, peak + 1.2))
    raise BuildError(f"Encoded audio failed loudness verification: {integrated} LUFS, {peak} dBTP.")


def master(video: Path, audio: Path, destination: Path, total_s: float, *,
           start_s: float = 0, preview: bool = False, reference: dict | None = None) -> dict:
    """Mux a full delivery or an informational excerpt, without releveling clips.

    With a reference, audio is the full normalized PCM and its sibling .m4a is
    the certified AAC. Full films copy that AAC; previews encode a PCM slice at
    the identical master gains. A standalone short input keeps its source gain.
    """
    delivery = not preview and total_s >= MIN_INTEGRATED_S
    if reference is None and delivery:
        source = audio
        audio = destination.parent / 'audio-master.wav'
        reference = prepare_audio_master(source, audio, total_s)
    if delivery and start_s != 0:
        raise BuildError("A delivery master must start at zero; use preview=True for excerpts.")
    source = audio.with_suffix('.m4a') if delivery else audio
    args = ["-i", video, "-ss", f"{start_s:.9f}", "-i", source,
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy"]
    args += (["-c:a", "copy"] if delivery else
             ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"])
    ffmpeg([*args, "-t", f"{total_s:.9f}", "-movflags", "+faststart", destination],
           destination.parent / 'mux.log')
    if delivery:
        verified = loudness(destination, destination.parent / 'loudness-delivery.log')
        if not delivery_ok(verified):
            raise BuildError(f"Encoded audio failed loudness verification: {verified['input_i']} LUFS, "
                             f"{verified['input_tp']} dBTP.")
        return {**reference, "measured_lufs": float(verified['input_i']),
                "true_peak_dbtp": float(verified['input_tp']), "verification": verified}
    report = loudness_report(destination, destination.parent / 'loudness-preview.log')
    return {**report, "integrated_gate": False,
            "gate_reason": "motiontest" if preview else "duration < 10 s",
            "normalization": "full_timeline_master" if reference else "source_gain",
            "reference": reference, "audio_start_s": start_s}


def validate_export(path: Path, expected_s: float) -> dict:
    info = probe(path)
    videos = [s for s in info["streams"] if s["codec_type"] == "video"]
    audios = [s for s in info["streams"] if s["codec_type"] == "audio"]
    actual = float(info["format"]["duration"])
    if len(videos) != 1 or len(audios) != 1:
        raise BuildError("Export must have exactly one video stream and one audio stream.")
    video, audio = videos[0], audios[0]
    if ((video["width"], video["height"]) != SIZE or Fraction(video["avg_frame_rate"]) != FPS
            or video["codec_name"] != "h264" or audio["codec_name"] != "aac"):
        raise BuildError("Export must be 1920×1080, 30 fps, H.264 + AAC.")
    if actual > 180 or abs(actual - expected_s) > 0.1:
        raise BuildError(f"Export is {actual:.3f} s (planned {expected_s:.3f} s); the limit is 180 s.")
    return {"duration_s": actual, "width": video["width"], "height": video["height"],
            "fps": str(video["avg_frame_rate"]), "video_codec": video["codec_name"], "audio_codec": audio["codec_name"]}
