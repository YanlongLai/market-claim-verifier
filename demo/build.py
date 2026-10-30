#!/usr/bin/env python3
"""Reproducible demo-video builder. v2 host gate 3: uv run --project demo python demo/build.py keyframes"""
from __future__ import annotations

import argparse
import dataclasses
import fcntl
import math
import os
import platform
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import PIL
import yaml

import media
from motion_timing import narration_lead
from pipeline import (BuildError, append_build_log, cache_key, cached, collapse, file_hash,
                      make_run_record, next_version, previous_run, read_json, receipt,
                      scene_timings, subtitle_timing, to_srt, voice_key, write_json)

DEMO = Path(__file__).resolve().parent
BREEZE = Path("/Users/yan/ml-engines/breeze-tts")


class Builder:
    def __init__(self, args: argparse.Namespace, demo: Path = DEMO):
        self.args = args
        self.demo = demo.resolve()
        self.repo = self.demo.parent
        self.cache = self.demo / "cache"
        self.storyboard = Path(args.storyboard).resolve() if args.storyboard else self.demo / "storyboard.yaml"
        try:
            self.story = yaml.safe_load(self.storyboard.read_text())
        except (OSError, yaml.YAMLError) as error:
            raise BuildError(f"Cannot read storyboard {self.storyboard}: {error}") from error
        self.validate_story()
        self.scenes = self.story["scenes"]
        available = {s["id"] for s in self.scenes}
        self.only = {part for value in args.only for part in value.split(",")} if args.only else available
        if self.only - available:
            raise BuildError(f"Unknown --only scene(s): {', '.join(sorted(self.only - available))}")
        self.pad = float(self.story.get("pad_s", 0.6))
        self.cache.mkdir(parents=True, exist_ok=True)
        self._versions = None

    def validate_story(self) -> None:
        story = self.story
        if not isinstance(story, dict) or not isinstance(story.get("scenes"), list) or not story["scenes"]:
            raise BuildError("storyboard.yaml must contain a nonempty scenes list.")
        if story.get("resolution") != [1920, 1080] or story.get("fps") != 30:
            raise BuildError("The delivery format is fixed at 1920×1080, 30 fps.")
        if any(s.get("visual", {}).get("kind") == "capture" for s in story["scenes"]):
            capture = story.get("capture")
            if not isinstance(capture, dict):
                raise BuildError("A capture configuration with viewport, scale, and color_scheme is required.")
            viewport = capture.get("viewport")
            if (not isinstance(viewport, list) or len(viewport) != 2
                    or any(type(size) is not int or size <= 0 for size in viewport)):
                raise BuildError("capture.viewport must contain two positive integer CSS dimensions.")
            scale = capture.get("scale")
            if type(scale) not in (int, float) or not math.isfinite(scale) or scale <= 0:
                raise BuildError("capture.scale must be a positive, finite number.")
            if capture.get("color_scheme") not in ("dark", "light", "no-preference"):
                raise BuildError("capture.color_scheme must be dark, light, or no-preference.")
        seen = set()
        for scene in story["scenes"]:
            sid = scene.get("id", "")
            if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", sid) or sid in seen:
                raise BuildError(f"Invalid or duplicate scene id: {sid}")
            seen.add(sid)
            for name in ("narration", "on_screen"):
                if not isinstance(scene.get(name), str) or not collapse(scene[name]):
                    raise BuildError(f"{sid}: {name} must be nonempty text.")
            try:
                target = float(scene["target_s"])
            except (KeyError, ValueError, TypeError) as error:
                raise BuildError(f"{sid}: target_s must be a positive number.") from error
            if not math.isfinite(target) or target <= 0:
                raise BuildError(f"{sid}: target_s must be a positive number.")
            narration_lead(scene)
            if 'narration_lead_s' in scene and story.get('motion_variant') != 'v3':
                raise BuildError(f"{sid}: narration_lead_s requires motion_variant: v3.")
            kind = scene.get("visual", {}).get("kind")
            if kind not in ("image", "capture", "card", "motion"):
                raise BuildError(f"{sid}: unknown visual.kind {kind!r}")
            if (kind == "motion") != (story.get("version") == 2):
                raise BuildError("v2 requires motion visuals; use storyboard-v1.yaml for the old capture path.")
            if kind == "card" and not re.fullmatch(r"[a-zA-Z0-9_-]+", scene["visual"].get("template", "")):
                raise BuildError(f"{sid}: invalid card template name.")
            if kind == "capture":
                self.capture_url(scene)
        if not isinstance(story.get("voice"), dict):
            raise BuildError("A voice configuration is required.")
        if story["voice"].get("mode", "design") not in ("clone", "design"):
            raise BuildError("voice.mode must be clone or design.")
        if story["voice"].get("mode") == "clone":
            config = story["voice"]
            if config.get("instruction"):
                raise BuildError("Clone mode uses the approved reference with no instruction.")
            reference = self.repo / config.get("ref_audio", "")
            if not reference.is_file() or reference.suffix.lower() != ".wav" or not config.get("ref_text", "").strip():
                raise BuildError("Clone mode requires voice.ref_audio WAV and voice.ref_text transcript.")
        if story.get("version") != 2 and float(story.get("pad_s", 0.6)) < media.CROSSFADE:
            raise BuildError("pad_s must be at least 0.4 s, so transitions cannot cut narration.")

    def selected(self, kind: str | None = None) -> list[dict]:
        return [s for s in self.scenes if s["id"] in self.only and (kind is None or s["visual"]["kind"] == kind)]

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.repo))
        except ValueError:
            return str(path)

    def capture_url(self, scene: dict) -> str:
        from urllib.parse import urlparse
        page = scene["visual"].get("page")
        if page not in ("site", "explorer"):
            raise BuildError(f"{scene['id']}: capture page must be site or explorer.")
        url = self.story.get(page + "_url", "")
        parsed = urlparse(url)
        if (parsed.scheme != "https" or parsed.netloc != "yanlonglai.github.io"
                or not parsed.path.startswith("/market-claim-verifier/")):
            raise BuildError("Network is restricted to https://yanlonglai.github.io/market-claim-verifier/…")
        return url

    def stage_dir(self, stage: str, sid: str, key: str) -> Path:
        directory = self.cache / stage / sid / key
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def alias(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        shutil.copy2(source, temporary)
        temporary.replace(destination)

    def versions(self) -> dict:
        if self._versions is None:
            playwright = media.command(["node", self.demo / "capture/browser.mjs", "--version"]).stdout.strip()
            self._versions = {
                "python": platform.python_version(),
                "ffmpeg": media.command([media.FFMPEG, "-version"]).stdout.splitlines()[0],
                "ffprobe": media.command([media.FFPROBE, "-version"]).stdout.splitlines()[0],
                "playwright": playwright,
                "node": media.command(["node", "--version"]).stdout.strip(),
                "pillow": PIL.__version__, "pyyaml": yaml.__version__,
            }
        return self._versions

    def engine(self) -> str:
        requested = self.story["voice"].get("engine")
        if requested in ("say", "macos-say"):
            return "macos-say"
        if requested != "breeze-tts-2":
            raise BuildError(f"Unknown voice engine {requested!r}; use breeze-tts-2 or say.")
        if (BREEZE / "run.sh").is_file() and os.access(BREEZE / "run.sh", os.X_OK):
            return "breeze-tts-2"
        if self.args.voice_fallback == "say":
            return "macos-say"
        raise BuildError(f"Breeze-TTS-2 is missing or not executable at {BREEZE / 'run.sh'}. "
                         "Finish its host installation, or pass --voice-fallback say for a Samantha draft.")

    def voice_spec(self, scene: dict) -> tuple[str, str, Path]:
        engine = self.engine()
        config = self.story["voice"]
        clone = config.get("mode") == "clone"
        key = voice_key(engine, config.get("instruction", ""), int(config.get("seed", 1234)), scene["narration"],
                        mode=config.get("mode", "design"),
                        ref_audio_sha256=file_hash(self.repo / config["ref_audio"]) if clone else None,
                        ref_text=config.get("ref_text") if clone else None)
        return engine, key, self.stage_dir("voice", scene["id"], key)

    def require_voice(self, scene: dict) -> dict:
        _, key, folder = self.voice_spec(scene)
        files = {"audio": folder / "clip.wav", "engine_receipt": folder / "source.wav.json"}
        result = cached(folder / "receipt.json", key, files)
        if not result:
            if self.story.get("version") == 2:
                raise BuildError(f"{scene['id']}: narration cache is missing or stale. Run voice for all "
                                 "motion shots on the host with the locked clone reference.")
            raise BuildError(f"{scene['id']}: narration cache is missing or stale. Run voice (with the same "
                             "--voice-fallback option), or run all without --only.")
        return result

    def voice(self) -> None:
        pending = []
        for scene in self.selected():
            engine, key, folder = self.voice_spec(scene)
            files = {"audio": folder / "clip.wav", "engine_receipt": folder / "source.wav.json"}
            if not self.args.force and cached(folder / "receipt.json", key, files):
                print(f"voice {scene['id']}: cached", flush=True)
                continue
            # An interrupted --force must never leave a receipt validating stale output.
            (folder / "receipt.json").unlink(missing_ok=True)
            pending.append((scene, engine, key, folder))
        if not pending:
            if self.story.get("version") == 2:
                self.prepare_motion()
            return
        engine = pending[0][1]
        if engine == "breeze-tts-2":
            jobs = [{"id": s["id"], "text": collapse(s["narration"]), "out": str(folder / "source.wav")}
                    for s, _, _, folder in pending]
            jobs_key = cache_key(jobs)
            jobs_file = self.cache / "voice" / f"jobs-{jobs_key}.json"
            write_json(jobs_file, jobs)
            config = self.story["voice"]
            reference_args = (["--ref-audio", self.repo / config["ref_audio"], "--ref-text", config["ref_text"]]
                              if config.get("mode") == "clone" else ["--instruction", config.get("instruction", "")])
            for _, _, _, folder in pending:
                (folder / "source.wav").unlink(missing_ok=True)
                (folder / "source.wav.json").unlink(missing_ok=True)
            print(f"voice: Breeze batch for {len(jobs)} scene(s), seed {config.get('seed', 1234)}", flush=True)
            try:
                media.command([BREEZE / "run.sh", "--device", "auto", "--jobs", jobs_file, *reference_args,
                               "--seed", str(config.get("seed", 1234))],
                              self.cache / "voice" / f"jobs-{jobs_key}.log")
            except BuildError as error:
                raise BuildError("Breeze-TTS-2 synthesis failed. Run on the host if its cache or MPS is unavailable "
                                 "in the sandbox. --voice-fallback say applies only when Breeze is missing.\n"
                                 + str(error)) from error
        for scene, engine, key, folder in pending:
            print(f"voice {scene['id']}: synthesizing ({engine})", flush=True)
            raw = folder / "source.wav"
            engine_receipt = folder / "source.wav.json"
            if engine == "macos-say":
                source = folder / "source.aiff"
                source.unlink(missing_ok=True)
                media.command(["say", "-v", "Samantha", "-o", source, collapse(scene["narration"])], folder / "say.log")
                media.normalize_voice(source, raw)
                write_json(engine_receipt, {"engine": "macos-say", "voice": "Samantha", "draft_only": True,
                                           "text": collapse(scene["narration"]), "sample_rate": 24000, "channels": 1,
                                           "instruction_supported": False, "seed_supported": False})
            if not engine_receipt.is_file():
                raise BuildError(f"{scene['id']}: the engine did not write its required per-clip receipt {engine_receipt}")
            engine_data = read_json(engine_receipt)
            if engine_data.get("status", "ok") in ("failed", "error", "blocked"):
                raise BuildError(f"{scene['id']}: TTS receipt reports {engine_data.get('status')}: {engine_data.get('error', '')}")
            seconds = media.normalize_voice(raw, folder / "clip.wav")
            receipt(folder / "receipt.json", key, {"audio": folder / "clip.wav", "engine_receipt": engine_receipt},
                    scene_id=scene["id"], engine=engine, voice_s=seconds, draft_only=engine == "macos-say",
                    narration=collapse(scene["narration"]), engine_receipt=engine_data)
            self.alias(folder / "clip.wav", self.cache / "voice" / f"{scene['id']}.wav")
        if self.story.get("version") == 2:
            self.prepare_motion()

    def prepare_motion(self, *, require_voice: bool = False) -> dict:
        from motion_build import prepare
        return prepare(self, require_voice=require_voice)

    def keyframes(self) -> None:
        from motion_build import keyframes
        keyframes(self)

    def review_frames(self) -> None:
        from motion_build import review_frames
        review_frames(self)

    def motiontest(self) -> None:
        from motion_build import render
        render(self, test=True)

    def render(self) -> None:
        from motion_build import render
        render(self)

    def voicecheck(self) -> None:
        from voicecheck import compare_clips
        paths = self.args.audio or [Path(self.require_voice(s)["artifacts"]["audio"]["path"]) for s in self.scenes]
        report = compare_clips(paths, threshold=self.args.threshold)
        write_json(self.cache / "voicecheck.json", report)
        print(f"voicecheck: {report['backend']}; min pairwise similarity {report['min_pairwise_similarity']:.4f}; "
              f"threshold {report['threshold']:.4f}; {'PASS' if report['passed'] else 'FAIL'}", flush=True)
        if not report["passed"]:
            raise BuildError("Voice similarity is below threshold. Review demo/cache/voicecheck.json and listen on the host.")

    def timings(self, scenes: list[dict] | None = None):
        scenes = self.scenes if scenes is None else scenes
        return scene_timings(scenes, {s["id"]: self.require_voice(s)["voice_s"] for s in scenes}, pad_s=self.pad)

    def capture_spec(self, scene: dict, seconds: float) -> tuple[str, Path]:
        scripts = {p.name: file_hash(p) for p in (self.demo / "capture").glob("*.mjs")
                   if p.name in (scene["id"] + ".mjs", "common.mjs", "browser.mjs")}
        key = cache_key("capture-v2", self.capture_url(scene), scene["visual"], seconds,
                        scripts, self.versions()["playwright"], self.story["capture"], self.story["resolution"])
        return key, self.stage_dir("capture", scene["id"], key)

    def capture(self) -> None:
        for scene in self.selected("capture"):
            timing = self.timings([scene])[0]
            key, folder = self.capture_spec(scene, timing.final_s)
            webm, mp4 = folder / "clip.webm", folder / "clip.mp4"
            files = {"webm": webm, "mp4": mp4}
            if not self.args.force and cached(folder / "receipt.json", key, files):
                print(f"capture {scene['id']}: cached", flush=True)
            else:
                (folder / "receipt.json").unlink(missing_ok=True)
                job = folder / "job.json"
                write_json(job, {"id": scene["id"], "url": self.capture_url(scene), "focus": scene["visual"]["focus"],
                                 "emphasis": scene["visual"].get("emphasis"), "capture": self.story["capture"],
                                 "resolution": self.story["resolution"],
                                 "duration_s": timing.final_s, "output": str(folder / "raw.webm"),
                                 "receipt": str(folder / "browser.json")})
                print(f"capture {scene['id']}: recording live site ({timing.final_s:.3f} s)", flush=True)
                media.command(["node", self.demo / "capture" / f"{scene['id']}.mjs", job], folder / "capture.log")
                browser_data = read_json(folder / "browser.json")
                media.normalize_capture(folder / "raw.webm", webm, mp4, timing.final_s, browser_data["lead_s"])
                receipt(folder / "receipt.json", key, files, scene_id=scene["id"], url=self.capture_url(scene),
                        focus=scene["visual"]["focus"], final_s=timing.final_s, browser=browser_data)
            self.alias(webm, self.cache / "capture" / f"{scene['id']}.webm")
            self.alias(mp4, self.cache / "capture" / f"{scene['id']}.mp4")

    def image(self, scene: dict) -> tuple[str, Path]:
        from PIL import Image
        path = self.demo / "assets/img" / f"{scene['id']}.png"
        if not path.is_file():
            raise BuildError(f"Missing still {path}. Generate it from demo/prompts/img/{scene['id']}.md with image_gen; "
                             "the builder never generates or substitutes artwork.")
        with Image.open(path) as image:
            if image.format != "PNG" or image.size != (1920, 1080):
                raise BuildError(f"{path}: expected a 1920×1080 PNG, got {image.format} {image.size}.")
        return cache_key("image-v1", file_hash(path)), path

    def images(self) -> None:
        for scene in self.selected("image"):
            key, path = self.image(scene)
            folder = self.stage_dir("images", scene["id"], key)
            if self.args.force or not cached(folder / "receipt.json", key, {"image": path}):
                receipt(folder / "receipt.json", key, {"image": path}, generated_by="external-image_gen")
            print(f"images {scene['id']}: validated 1920×1080 PNG", flush=True)

    def card_spec(self, scene: dict) -> tuple[str, Path, Path]:
        template = self.demo / "cards" / (scene["visual"]["template"] + ".html")
        if not template.is_file():
            raise BuildError(f"Missing end-card template: {template}")
        scripts = [self.demo / "cards/render.mjs", self.demo / "capture/browser.mjs"]
        key = cache_key("card-v1", file_hash(template), [file_hash(p) for p in scripts], self.versions()["playwright"])
        folder = self.stage_dir("card", scene["id"], key)
        return key, folder, template

    def card(self) -> None:
        for scene in self.selected("card"):
            key, folder, template = self.card_spec(scene)
            png = folder / "card.png"
            if not self.args.force and cached(folder / "receipt.json", key, {"image": png}):
                print(f"card {scene['id']}: cached", flush=True)
            else:
                (folder / "receipt.json").unlink(missing_ok=True)
                print(f"card {scene['id']}: rendering HTML in Chromium", flush=True)
                media.command(["node", self.demo / "cards/render.mjs", template, png], folder / "render.log")
                receipt(folder / "receipt.json", key, {"image": png}, template=self.rel(template))
            self.alias(png, self.cache / "card" / f"{scene['id']}.png")

    def visual(self, scene: dict, seconds: float) -> tuple[str, Path, dict[str, Path]]:
        kind = scene["visual"]["kind"]
        if kind == "image":
            key, path = self.image(scene)
            return key, path, {"image": path}
        if kind == "capture":
            key, folder = self.capture_spec(scene, seconds)
            files = {"webm": folder / "clip.webm", "mp4": folder / "clip.mp4"}
            if not cached(folder / "receipt.json", key, files):
                raise BuildError(f"{scene['id']}: live capture is missing/stale. Run capture on the host; "
                                 "sandbox Chromium cannot record. No fake capture was substituted.")
            return key, files["mp4"], files
        key, folder, template = self.card_spec(scene)
        path = folder / "card.png"
        if not cached(folder / "receipt.json", key, {"image": path}):
            raise BuildError(f"{scene['id']}: card is missing/stale. Run card on the host with Chromium available.")
        return key, path, {"image": path, "template": template}

    def music(self) -> Path | None:
        config = self.story.get("music") or {}
        explicit = config.get("file") or config.get("path")
        if explicit:
            path = Path(explicit)
            path = path if path.is_absolute() else self.repo / path
            if not path.is_file():
                raise BuildError(f"Configured music is missing: {path}. Remove music.path to build without music.")
            return path
        candidates = list((self.cache / "music").glob("bed-*.wav"))
        return max(candidates, key=lambda p: (p.stat().st_mtime_ns, p.name), default=None)

    def assemble(self) -> dict:
        if self.story.get("version") == 2:
            raise BuildError("v2 uses render. Current gate: run keyframes on the host before motiontest/full render.")
        timings = self.timings()
        total = timings[-1].start_s + timings[-1].final_s
        if total > 180:
            raise BuildError(f"Storyboard measures {total:.3f} s, exceeding the 180 s hackathon limit. "
                             "Review narration/voice on the host; the builder never silently speeds up or cuts speech.")
        if total > float(self.story.get("target_total_s", 170)):
            print(f"WARNING: {total:.3f} s exceeds the storyboard's {self.story.get('target_total_s', 170)} s soft target.")
        for timing in timings:
            print(f"{timing.id}: voice {timing.voice_s:.3f} s; final {timing.final_s:.3f} s / target {timing.target_s:g} s"
                  + (f" — WARNING +{timing.over_budget_percent:.1f}%" if timing.over_budget_percent > 25 else ""), flush=True)
        music = self.music()
        if music is None:
            print("No demo/cache/music/bed-*.wav exists; assembling without music.", flush=True)
        else:
            media.duration(music)
            print(f"Music: {self.rel(music)}", flush=True)
        versions = self.versions()
        renderer_hash = cache_key(file_hash(self.demo / "media.py"), file_hash(self.demo / "pipeline.py"),
                                  file_hash(media.font_path()), versions["pillow"], versions["ffmpeg"])
        clips, voices, records, subtitles = [], [], [], []
        inputs = {"images": {}, "music": {}, "captures": {}, "narration": {}, "templates": {}}
        if music:
            inputs["music"][self.rel(music)] = file_hash(music)
        for scene, timing in zip(self.scenes, timings):
            sid = scene["id"]
            voice = self.require_voice(scene)
            voice_path = Path(voice["artifacts"]["audio"]["path"])
            visual_key, visual, visual_files = self.visual(scene, timing.final_s)
            render_key = cache_key("render-v1", visual_key, file_hash(visual), scene["on_screen"],
                                   collapse(scene["narration"]), timing.voice_s, timing.final_s, renderer_hash)
            folder = self.stage_dir("scene", sid, render_key)
            clip = folder / "clip.mp4"
            if not (cached(folder / "receipt.json", render_key, {"video": clip}) and
                    not (self.args.force and sid in self.only)):
                if sid not in self.only:
                    raise BuildError(f"{sid}: unselected scene needs rendering. Run all/assemble without --only first.")
                print(f"assemble {sid}: rendering subtitles, lower third, and visual", flush=True)
                (folder / "receipt.json").unlink(missing_ok=True)
                media.render_scene(visual, scene["visual"]["kind"], scene, timing, clip)
                receipt(folder / "receipt.json", render_key, {"video": clip}, scene_id=sid)
            else:
                print(f"assemble {sid}: cached", flush=True)
            clips.append(clip)
            voices.append(voice_path)
            subtitles += subtitle_timing(scene["narration"], timing.voice_s, timing.start_s)
            records.append({**dataclasses.asdict(timing), "engine": voice["engine"],
                            "cache_keys": {"voice": voice["key"], "visual": visual_key, "render": render_key}})
            inputs["narration"][self.rel(voice_path)] = file_hash(voice_path)
            engine_receipt = Path(voice["artifacts"]["engine_receipt"]["path"])
            inputs["narration"][self.rel(engine_receipt)] = file_hash(engine_receipt)
            for name, path in visual_files.items():
                group = "templates" if name == "template" else ("captures" if scene["visual"]["kind"] == "capture" else "images")
                inputs[group][self.rel(path)] = file_hash(path)
        gain = float((self.story.get("music") or {}).get("gain_db", -22))
        assembly_key = cache_key("assembly-v1", [(r["cache_keys"], file_hash(p)) for r, p in zip(records, clips)],
                                 [(file_hash(p), t.final_s) for p, t in zip(voices, timings)],
                                 file_hash(music) if music else None, gain, media.CROSSFADE, renderer_hash)
        folder = self.stage_dir("assemble", "full", assembly_key)
        master = folder / "master.mp4"
        assembly_receipt = cached(folder / "receipt.json", assembly_key, {"video": master})
        if assembly_receipt is None or self.args.force:
            (folder / "receipt.json").unlink(missing_ok=True)
            print("assemble: crossfades, narration/music mix, two-pass loudnorm", flush=True)
            media.join_visuals(clips, timings, folder / "picture.mp4")
            media.mix_audio(voices, timings, music, gain, folder / "mix.wav")
            loudness = media.master(folder / "picture.mp4", folder / "mix.wav", master, total)
            validation = media.validate_export(master, total)
            assembly_receipt = receipt(folder / "receipt.json", assembly_key, {"video": master},
                                       loudness=loudness, validation=validation)
        else:
            print("assemble: reusing cached master; recording a new export version", flush=True)
            media.validate_export(master, total)
        out, runs = self.demo / "out", self.demo / "runs"
        out.mkdir(parents=True, exist_ok=True)
        version = next_version(runs, out)
        output = out / f"demo-v{version:03}.mp4"
        srt = out / f"demo-v{version:03}.srt"
        srt.write_text(to_srt(subtitles))
        self.alias(master, output)
        run = make_run_record(version=version, storyboard=self.storyboard, scenes=records,
                              total_s=assembly_receipt["validation"]["duration_s"], inputs=inputs, versions=versions,
                              output=output, subtitles=srt, previous=previous_run(runs),
                              assembly_cache_key=assembly_key,
                              music_cache_key=cache_key(file_hash(music) if music else None, gain),
                              music_gain_db=gain, music_present=music is not None,
                              loudness=assembly_receipt["loudness"], validation=assembly_receipt["validation"],
                              draft_only=any(r["engine"] == "macos-say" for r in records),
                              timing_notes="Frame-rounded voice + pad_s; 0.4 s visual overlaps consume only narration silence. "
                                           "Subtitles use word-weighted timing estimates, not forced alignment.")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        write_json(runs / f"{timestamp}-v{version:03}.json", run)
        append_build_log(self.demo / "BUILD_LOG.md", run)
        print(f"Built {self.rel(output)} ({run['total_s']:.3f} s), plus {self.rel(srt)}", flush=True)
        return run


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=["voice", "capture", "images", "card", "assemble", "all",
                                         "keyframes", "review-frames", "motiontest", "render", "voicecheck"])
    cli.add_argument("--storyboard", type=Path, help="Alternate storyboard; outputs still live under demo/.")
    cli.add_argument("--force", action="store_true", help="Redo the selected stage(s), even if cached.")
    cli.add_argument("--only", action="append", default=[], metavar="SCENE", help="Scene id; repeat or comma-separate. Assemble still exports the full storyboard.")
    cli.add_argument("--voice-fallback", choices=["say"], help="If Breeze is missing, use Samantha (draft only).")
    cli.add_argument("--t", action="append", type=float, help="Absolute keyframe time in seconds; repeat. Defaults are 3, 65, 155 with v2c presentation holds.")
    cli.add_argument("--out", type=Path, help="Keyframe/review directory, or motiontest MP4. Full render stays versioned in demo/out/.")
    cli.add_argument("--prepare-only", action="store_true", help="review-frames: write cues, full-length SRT and PNG plan without launching Chromium.")
    cli.add_argument("--shot", default="m05", help="Motiontest shot id or unique prefix (default m05).")
    cli.add_argument("--len", type=float, default=2.0, help="Motiontest length in seconds (default 2).")
    cli.add_argument("--audio", action="append", type=Path, help="Voicecheck WAV; repeat (default: current narration clips).")
    cli.add_argument("--threshold", type=float, default=0.85, help="Minimum MFCC-mean cosine similarity (default .85).")
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    builder = None
    try:
        builder = Builder(args)
        if args.prepare_only and args.command != 'review-frames':
            raise BuildError('--prepare-only is only supported by review-frames.')
        with (builder.cache / "build.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise BuildError("Another demo build is running. Wait for it before modifying the same cache/export.") from error
            if args.command == "all":
                if builder.story.get("version") == 2:
                    raise BuildError("v2 is gated: run voice, then keyframes. motiontest and render require later Owner gates.")
                builder.voice()
                builder.capture()
                builder.card()
                builder.assemble()
            else:
                getattr(builder, args.command.replace('-', '_'))()
        return 0
    except (BuildError, OSError, ValueError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr, flush=True)
        if args.command in ("all", "assemble", "render", "motiontest"):
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            attempt = {"status": "failed", "created_at": stamp, "command": args.command, "error": str(error),
                       "only": args.only, "voice_fallback": args.voice_fallback}
            if builder:
                attempt["storyboard_sha256"] = file_hash(builder.storyboard)
            write_json(DEMO / "runs" / f"attempt-{stamp}.json", attempt)
        return 1


if __name__ == "__main__":
    sys.exit(main())
