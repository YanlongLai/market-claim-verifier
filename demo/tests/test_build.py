import json
import subprocess
from copy import deepcopy

import pytest
import yaml

import build
import media
from build import Builder, parser
from pipeline import BuildError, Timing, read_json, write_json


def story(tmp_path, **changes):
    demo = tmp_path / "demo"; demo.mkdir()
    data = {"resolution":[1920,1080], "fps":30, "voice":{"engine":"breeze-tts-2", "seed":1234, "instruction":"calm"},
            "capture":{"viewport":[1280,720], "scale":1.5, "color_scheme":"dark"},
            "scenes":[{"id":"s01", "target_s":4, "narration":"A real number.", "on_screen":"Check the number", "visual":{"kind":"image"}}]}
    data.update(changes)
    (demo / "storyboard.yaml").write_text(yaml.safe_dump(data))
    return demo


def test_missing_breeze_requires_explicit_draft_fallback(tmp_path, monkeypatch):
    demo = story(tmp_path)
    monkeypatch.setattr(build, "BREEZE", tmp_path / "absent-engine")
    builder = Builder(parser().parse_args(["voice"]), demo)
    with pytest.raises(BuildError, match="--voice-fallback say"):
        builder.engine()
    draft = Builder(parser().parse_args(["voice", "--voice-fallback", "say"]), demo)
    assert draft.engine() == "macos-say"


def test_capture_rejects_unapproved_network_and_scene_ids(tmp_path):
    scenes = [{"id":"s01", "target_s":4, "narration":"Claim.", "on_screen":"Number", "visual":{"kind":"capture", "page":"site", "focus":"hero"}}]
    demo = story(tmp_path, scenes=scenes, site_url="https://example.com/")
    with pytest.raises(BuildError, match="Network is restricted"):
        Builder(parser().parse_args(["capture"]), demo)
    data = yaml.safe_load((demo / "storyboard.yaml").read_text())
    data["site_url"] = "https://yanlonglai.github.io/market-claim-verifier/site/"
    (demo / "storyboard.yaml").write_text(yaml.safe_dump(data))
    with pytest.raises(BuildError, match="Unknown --only"):
        Builder(parser().parse_args(["capture", "--only", "typo"]), demo)


@pytest.mark.parametrize("change", [{}, {"viewport":[960,540]}, {"scale":2}, {"color_scheme":"light"}])
def test_capture_settings_flow_from_storyboard_to_cache_job_and_browser(tmp_path, monkeypatch, change):
    source = yaml.safe_load((build.DEMO / "storyboard-v1.yaml").read_text())
    assert source["capture"] == {"viewport":[1280,720], "scale":1.5, "color_scheme":"dark"}
    scene = next(s for s in source["scenes"] if s["id"] == "s02-problem")
    demo = story(tmp_path, scenes=[scene], capture=deepcopy(source["capture"]), site_url=source["site_url"])
    builder = Builder(parser().parse_args(["capture"]), demo)
    builder._versions = {"playwright":"1.64.fixture"}
    monkeypatch.setattr(builder, "engine", lambda: "breeze-tts-2")
    monkeypatch.setattr(builder, "timings", lambda scenes: [Timing(scene["id"],15,2,2.6,0,0)])
    old_capture_key = builder.capture_spec(scene, 2.6)[0]
    old_voice_key = builder.voice_spec(scene)[1]
    builder.story["capture"].update(change)
    assert (builder.capture_spec(scene, 2.6)[0] != old_capture_key) == bool(change)
    assert builder.voice_spec(scene)[1] == old_voice_key

    jobs = []
    def record(args, log):
        job = read_json(args[-1])
        jobs.append(job)
        # Exercise the actual JS options factory without importing or launching Chromium.
        script = """
            import {readFileSync} from 'node:fs';
            const {captureContextOptions} = await import(process.argv[1]);
            console.log(JSON.stringify(captureContextOptions(JSON.parse(readFileSync(0, 'utf8')))));
        """
        options = json.loads(subprocess.run(
            ["node", "--input-type=module", "-e", script, (build.DEMO / "capture/common.mjs").as_uri()],
            input=json.dumps(job), text=True, capture_output=True, check=True).stdout)
        settings = builder.story["capture"]
        assert job["capture"] == settings
        assert job["resolution"] == source["resolution"]
        assert job["emphasis"] == "without"
        assert options["viewport"] == dict(zip(("width","height"), settings["viewport"]))
        assert options["screen"] == options["viewport"]
        assert options["deviceScaleFactor"] == settings["scale"]
        assert options["colorScheme"] == settings["color_scheme"]
        assert options["recordVideo"]["size"] == {"width":1920,"height":1080}
        write_json(args[-1].parent / "browser.json", {"lead_s":0.2})

    def normalize(source, webm, mp4, seconds, lead_s):
        assert seconds == 2.6 and lead_s == 0.2
        webm.write_bytes(b"test fixture, not live footage")
        mp4.write_bytes(b"test fixture, not live footage")

    monkeypatch.setattr(media, "command", record)
    monkeypatch.setattr(media, "normalize_capture", normalize)
    builder.capture()
    builder.capture()
    assert len(jobs) == 1  # The unchanged second capture uses its receipt.


@pytest.mark.parametrize("field,value", [
    ("viewport",[1920]), ("viewport",[True,720]), ("viewport",[0,720]),
    ("scale",0), ("scale",float("inf")), ("color_scheme","sepia"),
])
def test_invalid_capture_settings_fail_before_browser_launch(tmp_path, field, value):
    scene = {"id":"s01", "target_s":4, "narration":"Claim.", "on_screen":"Number",
             "visual":{"kind":"capture", "page":"site", "focus":"hero"}}
    settings = {"viewport":[1280,720], "scale":1.5, "color_scheme":"dark", field:value}
    demo = story(tmp_path, scenes=[scene], capture=settings)
    with pytest.raises(BuildError, match=f"capture.{field}"):
        Builder(parser().parse_args(["capture"]), demo)


def test_chart_scenes_use_the_english_site_with_opposite_emphasis():
    source = yaml.safe_load((build.DEMO / "storyboard-v1.yaml").read_text())
    scenes = {s["id"]:s for s in source["scenes"]}
    assert scenes["s02-problem"]["visual"] == {
        "kind":"capture", "page":"site", "focus":"#chart", "emphasis":"without"}
    assert scenes["s08-results"]["visual"] == {
        "kind":"capture", "page":"site", "focus":"#results", "emphasis":"with-checks"}


def test_capture_shot_sequence_without_a_browser():
    result = subprocess.run(["node", "--test", str(build.DEMO / "tests/capture.test.mjs")],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_newest_music_and_explicit_music_path(tmp_path):
    demo = story(tmp_path)
    folder = demo / "cache/music"; folder.mkdir(parents=True)
    old, new = folder / "bed-old.wav", folder / "bed-new.wav"
    old.write_bytes(b"old"); new.write_bytes(b"new")
    import os
    os.utime(old, (1,1)); os.utime(new, (2,2))
    builder = Builder(parser().parse_args(["images"]), demo)
    assert builder.music() == new
    builder.story["music"] = {"path":"demo/cache/music/bed-old.wav"}
    assert builder.music() == old
    builder.story["music"]["path"] = "missing.wav"
    with pytest.raises(BuildError, match="Configured music is missing"):
        builder.music()


def test_limit_fails_before_any_media_is_rendered(tmp_path, monkeypatch):
    demo = story(tmp_path)
    builder = Builder(parser().parse_args(["assemble"]), demo)
    monkeypatch.setattr(builder, "timings", lambda: [Timing("s01", 170, 181, 181.6, 0, 7)])
    with pytest.raises(BuildError, match="180 s"):
        builder.assemble()
    assert not (demo / "out").exists()


def test_assembly_only_is_a_full_export_with_selected_cache_invalidation(tmp_path, monkeypatch):
    from PIL import Image
    from pipeline import receipt

    scenes = [{"id":sid, "target_s":3, "narration":"Check this number.", "on_screen":"Original caption", "visual":{"kind":"image"}}
              for sid in ("s01", "s02")]
    demo = story(tmp_path, scenes=scenes, voice={"engine":"say"})
    (demo / "assets/img").mkdir(parents=True)
    for sid in ("s01", "s02"):
        Image.new("RGB", (1920,1080), "#111a20").save(demo / "assets/img" / f"{sid}.png")
    # Test-only fixtures stay inside pytest's temporary demo, never the real demo cache/out.
    for name in ("media.py", "pipeline.py"):
        (demo / name).write_text("fixture renderer source")
    monkeypatch.setattr(Builder, "versions", lambda self: {"python":"test", "ffmpeg":"test", "playwright":"1.64.fixture", "pillow":"test"})
    builder = Builder(parser().parse_args(["assemble"]), demo)
    for scene in scenes:
        engine, key, folder = builder.voice_spec(scene)
        audio = folder / "clip.wav"; audio.write_bytes(b"fixture, not narration")
        source_receipt = folder / "source.wav.json"; source_receipt.write_text('{}')
        receipt(folder / "receipt.json", key, {"audio":audio,"engine_receipt":source_receipt}, voice_s=2, engine=engine)
    rendered = []
    def render(visual, kind, scene, timing, destination):
        rendered.append(scene["id"]); destination.write_bytes(scene["on_screen"].encode())
    def join(clips, timings, destination):
        destination.write_bytes(b"joined picture")
    def mix(voices, timings, music, gain, destination):
        destination.write_bytes(b"mixed audio")
    def master(picture, audio, destination, total):
        destination.write_bytes(b"fixture export"); return {"measured_lufs":-14,"true_peak_dbtp":-2}
    monkeypatch.setattr(media, "render_scene", render)
    monkeypatch.setattr(media, "join_visuals", join)
    monkeypatch.setattr(media, "mix_audio", mix)
    monkeypatch.setattr(media, "master", master)
    monkeypatch.setattr(media, "validate_export", lambda path,total: {"duration_s":total})
    first = builder.assemble()
    assert rendered == ["s01", "s02"]
    rendered.clear()
    second = Builder(parser().parse_args(["assemble"]), demo).assemble()
    assert second["version"] == 2 and not rendered
    data = yaml.safe_load((demo / "storyboard.yaml").read_text())
    data["scenes"][1]["on_screen"] = "Revised caption"
    (demo / "storyboard.yaml").write_text(yaml.safe_dump(data))
    third = Builder(parser().parse_args(["assemble","--only","s02"]), demo).assemble()
    assert rendered == ["s02"]
    assert [s["id"] for s in third["scenes"]] == ["s01","s02"]
    assert third["changes_since_previous"] == {"s02":["render"]}
    assert len(list((demo / "runs").glob('*-v*.json'))) == 3
    assert (demo / "out/demo-v003.srt").is_file()
