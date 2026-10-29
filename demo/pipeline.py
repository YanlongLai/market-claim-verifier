"""Pure helpers for cache identity, frame timing, subtitles, and build records."""
from __future__ import annotations

import hashlib
import json
import math
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class BuildError(RuntimeError):
    """An actionable build failure, without an internal traceback."""


def collapse(text: str) -> str:
    return " ".join(text.split())


def cache_key(*parts: Any) -> str:
    """Canonical JSON prevents ambiguous concatenation and dictionary-order drift."""
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def voice_key(engine: str, instruction: str, seed: int, text: str, *, mode: str = "design",
              ref_audio_sha256: str | None = None, ref_text: str | None = None) -> str:
    if mode == "clone":
        if not ref_audio_sha256 or not ref_text or not ref_text.strip():
            raise BuildError("Clone cache identity requires the reference audio hash and transcript.")
        return cache_key("voice-clone-v2", engine, ref_audio_sha256, ref_text, seed, collapse(text))
    if mode != "design":
        raise BuildError(f"Unknown voice mode: {mode}")
    # Preserve every v1 voice cache key.
    return cache_key(engine, instruction, seed, collapse(text))


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def cached(path: Path, key: str, files: dict[str, Path]) -> dict | None:
    """A receipt is valid only while all artifact hashes still match."""
    if not path.is_file():
        return None
    try:
        receipt = read_json(path)
        if receipt["key"] != key:
            return None
        for name, artifact in files.items():
            if not artifact.is_file() or artifact.stat().st_size == 0:
                return None
            if receipt["artifacts"][name]["sha256"] != file_hash(artifact):
                return None
        return receipt
    except (OSError, KeyError, ValueError, TypeError):
        return None


def receipt(path: Path, key: str, files: dict[str, Path], **details: Any) -> dict:
    result = {
        "key": key,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": {name: {"path": str(p), "sha256": file_hash(p)} for name, p in files.items()},
        **details,
    }
    write_json(path, result)
    return result


@dataclass(frozen=True)
class Timing:
    id: str
    target_s: float
    voice_s: float
    final_s: float
    start_s: float
    over_budget_percent: float


def scene_timings(scenes: list[dict], durations: dict[str, float], fps: int = 30,
                  pad_s: float = 0.6, crossfade_s: float = 0.4) -> list[Timing]:
    if fps <= 0 or pad_s < crossfade_s or crossfade_s < 0:
        raise BuildError("Use fps > 0 and pad_s >= crossfade_s >= 0, so transitions cannot cut narration.")
    timings = []
    start = 0.0
    for scene in scenes:
        voice_s = durations[scene["id"]]
        target = float(scene["target_s"])
        if not math.isfinite(voice_s) or voice_s <= 0 or not math.isfinite(target) or target <= 0:
            raise BuildError(f"{scene['id']}: narration and target durations must be positive and finite.")
        final = math.ceil((voice_s + pad_s) * fps - 1e-8) / fps
        timings.append(Timing(scene["id"], target, voice_s, final, round(start, 9), (final / target - 1) * 100))
        start += final - crossfade_s
    return timings


@dataclass(frozen=True)
class Subtitle:
    start: float
    end: float
    text: str


def subtitle_chunks(text: str, width: int = 42) -> list[str]:
    """Preserve all words; prefer sentence boundaries and balance two-line cues."""
    text = collapse(text)
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?])\s+(?=[\w"“])', text)
    cues = []
    for sentence in sentences:
        lines = textwrap.wrap(sentence, width=width, break_long_words=True, break_on_hyphens=False)
        while lines:
            pair, lines = lines[:2], lines[2:]
            # Balance two lines without exceeding the character limit.
            if len(pair) == 2:
                words = " ".join(pair).split()
                choices = [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]
                choices = [p for p in choices if max(map(len, p)) <= width]
                if choices:
                    pair = list(min(choices, key=lambda p: abs(len(p[0]) - len(p[1]))))
            cues.append("\n".join(pair))
    return cues


def subtitle_timing(text: str, duration: float, offset: float = 0) -> list[Subtitle]:
    """Word-weighted estimates: TTS does not promise forced-alignment timestamps."""
    chunks = subtitle_chunks(text)
    if not chunks:
        return []
    if duration <= 0 or not math.isfinite(duration):
        raise BuildError("Subtitle duration must be positive and finite.")
    weights = [max(1, len(re.findall(r"\S+", chunk))) for chunk in chunks]
    total = sum(weights)
    elapsed = 0
    result = []
    for chunk, weight in zip(chunks, weights):
        start = offset + duration * elapsed / total
        elapsed += weight
        end = offset + duration * elapsed / total
        result.append(Subtitle(start, end, chunk))
    return result


def srt_timestamp(seconds: float) -> str:
    ms = round(max(0, seconds) * 1000)
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def to_srt(subtitles: list[Subtitle]) -> str:
    return "".join(f"{i}\n{srt_timestamp(cue.start)} --> {srt_timestamp(cue.end)}\n{cue.text}\n\n"
                   for i, cue in enumerate(subtitles, 1))


def next_version(runs: Path, out: Path) -> int:
    """Count records AND media, so an interrupted build never overwrites an export."""
    versions = []
    for folder in (runs, out):
        if folder.exists():
            for path in folder.iterdir():
                match = re.search(r"(?:^|-)v(\d+)\.(?:json|mp4|srt)$", path.name)
                if match:
                    versions.append(int(match.group(1)))
    return max(versions, default=0) + 1


def previous_run(runs: Path) -> dict | None:
    records = []
    for path in runs.glob("*-v*.json"):
        try:
            record = read_json(path)
            records.append(record)
        except (OSError, ValueError):
            continue
    return max(records, key=lambda r: r.get("version", 0), default=None)


def changed_scenes(current: list[dict], previous: dict | None) -> dict[str, list[str]]:
    old = {scene["id"]: scene for scene in (previous or {}).get("scenes", [])}
    changes = {}
    for scene in current:
        before = old.get(scene["id"], {}).get("cache_keys", {})
        names = sorted(k for k, value in scene["cache_keys"].items() if before.get(k) != value)
        if names:
            changes[scene["id"]] = names
    for removed in old.keys() - {s["id"] for s in current}:
        changes[removed] = ["removed"]
    return changes


def make_run_record(*, version: int, storyboard: Path, scenes: list[dict], total_s: float,
                    inputs: dict, versions: dict, output: Path, subtitles: Path,
                    previous: dict | None, **details: Any) -> dict:
    return {
        "schema_version": 1,
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "storyboard": {"path": str(storyboard), "sha256": file_hash(storyboard)},
        "scenes": scenes,
        "total_s": total_s,
        "input_files": inputs,
        "tool_versions": versions,
        "output": {"path": str(output), "sha256": file_hash(output)},
        "subtitles": {"path": str(subtitles), "sha256": file_hash(subtitles)},
        "changes_since_previous": changed_scenes(scenes, previous),
        "global_cache_changes": [name for name, value in details.items() if name.endswith("_cache_key")
                                 and (previous or {}).get(name) != value],
        **details,
    }


def append_build_log(path: Path, run: dict) -> None:
    if not path.exists():
        path.write_text("# Demo build log\n\nSuccessful assembles are appended automatically. See runs/ for complete records.\n")
    over = [f"{s['id']} (+{s['over_budget_percent']:.1f}%)" for s in run["scenes"] if s["over_budget_percent"] > 25]
    changes = "; ".join(f"{sid}: {', '.join(keys)}" for sid, keys in run["changes_since_previous"].items()) or "none (cache reused)"
    with path.open("a") as stream:
        stream.write(f"\n## v{run['version']:03} — {run['created_at']}\n\n"
                     f"Length: {run['total_s']:.3f} s. Scenes >25% over budget: {', '.join(over) or 'none'}.\n\n"
                     f"Changed scene cache keys: {changes}.\n\n"
                     f"Changed global cache keys: {', '.join(run.get('global_cache_changes', [])) or 'none'}.\n\n"
                     f"Output: `{run['output']['path']}`; SHA-256 `{run['output']['sha256']}`.\n")
