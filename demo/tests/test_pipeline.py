import pytest

from pipeline import (BuildError, append_build_log, cache_key, cached, changed_scenes,
                      collapse, file_hash, make_run_record, next_version, read_json,
                      receipt, scene_timings, srt_timestamp, subtitle_chunks,
                      subtitle_timing, to_srt, voice_key, write_json)


def test_cache_keys_are_unambiguous_stable_and_content_sensitive():
    assert cache_key({"a": 1, "b": 2}) == cache_key({"b": 2, "a": 1})
    assert cache_key("ab", "c") != cache_key("a", "bc")
    assert cache_key("中文") != cache_key("English")
    assert len(cache_key("x")) == 64
    base = voice_key("breeze-tts-2", "calm", 1234, "Hello,\n  world.")
    assert base == voice_key("breeze-tts-2", "calm", 1234, "Hello, world.")
    for args in [("macos-say", "calm", 1234, "Hello, world."),
                 ("breeze-tts-2", "fast", 1234, "Hello, world."),
                 ("breeze-tts-2", "calm", 99, "Hello, world."),
                 ("breeze-tts-2", "calm", 1234, "Other words.")]:
        assert voice_key(*args) != base


def test_cache_receipt_rejects_missing_corrupt_and_modified_artifacts(tmp_path):
    artifact = tmp_path / "clip.wav"
    artifact.write_bytes(b"fixture audio")
    manifest = tmp_path / "receipt.json"
    receipt(manifest, "key", {"audio": artifact})
    assert cached(manifest, "key", {"audio": artifact})
    assert not cached(manifest, "different", {"audio": artifact})
    artifact.write_bytes(b"damaged audio")
    assert not cached(manifest, "key", {"audio": artifact})
    artifact.unlink()
    assert not cached(manifest, "key", {"audio": artifact})
    manifest.write_text("partial json")
    assert not cached(manifest, "key", {"audio": artifact})


@pytest.mark.parametrize("text", [
    'Ask a language model on its own, and it guesses. "Is this right?" We check every number.',
    'With tools and program checks, accuracy rises to eighty-three percent on the Meta Model API, '
    'and ninety point five percent with open-weight Muse Spark on Baseten and Fireworks.',
    '中文單位也能檢查，包括「億」。 Every number, every claim, every original filing.',
    'x'*170,
])
def test_subtitles_never_exceed_two_lines_or_42_characters(text):
    chunks = subtitle_chunks(text)
    assert chunks
    assert all(1 <= len(chunk.splitlines()) <= 2 for chunk in chunks)
    assert all(len(line) <= 42 for chunk in chunks for line in chunk.splitlines())
    if " " in text:
        assert collapse(" ".join(chunks)) == collapse(text)
    else:
        assert "".join(chunks).replace("\n", "") == text


def test_subtitle_timing_is_monotonic_offset_and_ends_with_narration():
    cues = subtitle_timing("One short sentence. This is a longer sentence with more words. Finally, proof.", 8.2, 12.4)
    assert cues[0].start == 12.4
    assert cues[-1].end == pytest.approx(20.6)
    assert all(c.end > c.start for c in cues)
    assert all(a.end == pytest.approx(b.start) for a, b in zip(cues, cues[1:]))
    assert to_srt(cues).startswith("1\n00:00:12,400 --> ")
    assert srt_timestamp(59.9996) == "00:01:00,000"
    assert srt_timestamp(3600.05) == "01:00:00,050"
    assert subtitle_timing("  ", 3) == []


def test_crossfades_consume_padding_and_never_overlap_speech():
    scenes = [{"id":"a", "target_s":3}, {"id":"b", "target_s":4}]
    timings = scene_timings(scenes, {"a":2.013, "b":3.4})
    first, second = timings
    assert first.final_s == pytest.approx(79/30)
    assert second.start_s == pytest.approx(first.final_s-.4)
    assert second.start_s > first.voice_s
    assert second.start_s+second.final_s == pytest.approx(first.final_s+second.final_s-.4)
    assert first.over_budget_percent == pytest.approx((first.final_s/3-1)*100)
    cues_a = subtitle_timing("First scene ends.", first.voice_s, first.start_s)
    cues_b = subtitle_timing("Second scene starts.", second.voice_s, second.start_s)
    assert cues_a[-1].end < cues_b[0].start
    with pytest.raises(BuildError, match="pad_s"):
        scene_timings(scenes, {"a":2, "b":3}, pad_s=.2)


def test_versioning_includes_orphaned_exports_but_not_failed_attempts(tmp_path):
    runs, out = tmp_path / "runs", tmp_path / "out"
    assert next_version(runs, out) == 1
    runs.mkdir(); out.mkdir()
    (runs / "20261028T010000Z-v002.json").write_text("{}")
    (runs / "attempt-20261028T020000Z.json").write_text("{}")
    (out / "demo-v005.srt").write_text("")
    (out / "demo-v004.mp4").write_bytes(b"x")
    (out / "master-v999.mp4.tmp").write_bytes(b"partial")
    assert next_version(runs, out) == 6


def test_run_record_hashes_provenance_and_reports_only_changed_scene(tmp_path):
    story, output, srt = [tmp_path / name for name in ("storyboard.yaml", "demo-v002.mp4", "demo-v002.srt")]
    story.write_text("scenes: []\n"); output.write_bytes(b"fixture"); srt.write_text("subtitle\n")
    before = [{"id":"a", "cache_keys":{"voice":"a1", "visual":"v1"}},
              {"id":"b", "cache_keys":{"voice":"b1", "visual":"v2"}}]
    scenes = [{"id":"a", "target_s":2, "voice_s":2, "final_s":2.6, "over_budget_percent":30,
               "engine":"macos-say", "cache_keys":{"voice":"a2", "visual":"v1"}},
              {"id":"b", "target_s":3, "voice_s":2, "final_s":2.6, "over_budget_percent":-13,
               "engine":"macos-say", "cache_keys":{"voice":"b1", "visual":"v2"}}]
    run = make_run_record(version=2, storyboard=story, scenes=scenes, total_s=4.8,
                          inputs={"music":{"bed.wav":"hash"}}, versions={"ffmpeg":"9", "playwright":"1.64"},
                          output=output, subtitles=srt, previous={"scenes":before})
    assert run["output"]["sha256"] == file_hash(output)
    assert run["storyboard"]["sha256"] == file_hash(story)
    assert run["changes_since_previous"] == {"a":["voice"]}
    assert run["input_files"]["music"]["bed.wav"] == "hash"
    path = tmp_path / "run.json"; write_json(path, run)
    assert read_json(path) == run
    log = tmp_path / "BUILD_LOG.md"; append_build_log(log, run)
    assert "v002" in log.read_text() and "a (+30.0%)" in log.read_text()
    assert "a: voice" in log.read_text()
    assert changed_scenes([], {"scenes":before}) == {"a":["removed"], "b":["removed"]}
