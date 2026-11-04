"""Offline evidence, clean rebuild and paid-recorder boundaries for W3.

Synthetic encoding below tests FFmpeg determinism, not Breeze/OCR/ASR quality.
"""
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import wave

from PIL import Image
from pypdf import PdfReader
import pytest

from scripts import build_examples as assets
from scripts import run_example_records as recorder

ROOT = Path(__file__).resolve().parents[1]


def isolate(tmp_path, monkeypatch):
    for directory in ("docs/examples", "tests/fixtures/sec-offline"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    # This fixture deliberately has no host recording files. Keep its catalogue
    # in that same state, including when the real catalogue has saved links.
    catalogue = tmp_path / "docs/examples/manifest.json"
    rows = json.loads(catalogue.read_text())
    for row in rows:
        row["saved_result"] = None
    catalogue.write_bytes(assets.encoded(rows))
    monkeypatch.setattr(assets, "ROOT", tmp_path)
    monkeypatch.setattr(assets, "EXAMPLES", tmp_path / "docs/examples")
    monkeypatch.setattr(recorder, "ROOT", tmp_path)
    return assets.EXAMPLES


def test_fifteen_ids_hashes_one_story_per_five_formats_and_native_pdf():
    rows = json.loads((assets.EXAMPLES / "manifest.json").read_text())
    assert [r["id"] for r in rows] == list(recorder.IDS)
    assert len({r["id"] for r in rows}) == 15
    assert len([r for r in rows if r["kind"] in {"text", "image", "pdf"} and r["status"] == "ready"]) == 9
    for story in assets.load_stories():
        text = (assets.EXAMPLES / f"{story['id']}.txt").read_text()
        assert text == story["text"] and len(text) <= 600
        group = [r for r in rows if r["story"] == story["id"]]
        assert {r["kind"] for r in group} == set(assets.KINDS)
        assert len({r["text_sha256"] for r in group}) == 1
        for row in group:
            path = assets.EXAMPLES / row["file"]
            assert row["url"] == "/examples/" + path.name
            assert row["size_bytes"] == path.stat().st_size <= 2_000_000
            assert row["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
            assert row["fixture_citations"] == story["fixture_citations"]
            assert set(row["contains"]) == {"en", "zh"}
            assert row["saved_result"] == recorder.check_saved(row)  # Never invent a recorded envelope.
            if row["status"] == "pending":
                assert row["file"].endswith(".pending.txt") and row["duration_s"] is None
                assert assets.HOST_COMMAND in path.read_text()
                assert not (assets.EXAMPLES / row["target_file"]).exists()
            elif row["kind"] in {"audio", "video"}:
                assert 0 < row["duration_s"] <= 20
        with Image.open(assets.EXAMPLES / f"{story['id']}.png") as image:
            assert image.size == (1280, 720)
        pdf = PdfReader(assets.EXAMPLES / f"{story['id']}.pdf")
        assert len(pdf.pages) == 1
        assert " ".join(pdf.pages[0].extract_text().split()) == " ".join(text.split())
        face = pdf.pages[0]["/Resources"]["/Font"]["/F1"]
        assert face["/BaseFont"] == "/NotoSerifTC-Regular" and "/FontFile2" in face["/FontDescriptor"]


def test_clean_rebuild_is_byte_identical_without_model_network_or_host_tools(tmp_path, monkeypatch):
    folder = isolate(tmp_path, monkeypatch)
    monkeypatch.setattr(assets.subprocess, "run", lambda *a, **k: pytest.fail("host command in offline rebuild"))
    monkeypatch.setattr(assets.subprocess, "check_output", lambda *a, **k: pytest.fail("host probe in offline rebuild"))
    before = {p.relative_to(folder): p.read_bytes() for p in folder.rglob("*") if p.is_file()}
    # Remove generated outputs: a builder that merely preserves PNG/PDF cannot pass.
    for name in ("manifest.json", *(f"{s}.{ext}" for s in "abc" for ext in ("txt", "png", "pdf", "mp3.pending.txt", "mp4.pending.txt"))):
        (folder / name).unlink(missing_ok=True)
    for _ in range(2):
        assets.build()
        assets.build(check=True)
        assert {p.relative_to(folder): p.read_bytes() for p in folder.rglob("*") if p.is_file()} == before


def test_pending_notices_follow_media_readiness_and_check_rejects_stale_notices(tmp_path, monkeypatch):
    folder = isolate(tmp_path, monkeypatch)
    assert all(row["status"] == "ready" for row in assets.build(check=True))
    assert not list(folder.glob("*.pending.txt"))
    notice = folder / "a.mp3.pending.txt"
    notice.write_text("stale notice")
    with pytest.raises(ValueError, match="Stale pending notice"):
        assets.build(check=True)
    assets.build()
    assert not notice.exists()
    metadata = folder / "narration/a.json"
    retained_metadata, retained_audio = metadata.read_bytes(), (folder / "a.mp3").read_bytes()
    pending = json.loads(retained_metadata)
    del pending["outputs"]["audio"]
    metadata.write_bytes(assets.encoded(pending))
    (folder / "a.mp3").unlink()
    rows = assets.build()
    assert [row["id"] for row in rows if row["status"] == "pending"] == ["a-audio"]
    assert notice.is_file() and assets.HOST_COMMAND in notice.read_text()
    assets.build(check=True)
    metadata.write_bytes(retained_metadata)
    (folder / "a.mp3").write_bytes(retained_audio)
    assets.build()
    assets.build(check=True)
    assert not list(folder.glob("*.pending.txt"))


def test_each_number_resolves_to_hash_checked_fixture_and_c_unit_error_is_exact():
    stories = {s["id"]: s for s in assets.load_stories()}
    for story in stories.values():
        for number in story["fixture_citations"]:
            for source in number["sources"]:
                raw = (ROOT / source["fixture_path"]).read_bytes()
                assert source["fixture_sha256"] == hashlib.sha256(raw).hexdigest()
                row = json.loads(raw)
                for part in source["json_pointer"].strip("/").split("/"):
                    row = row[int(part)] if isinstance(row, list) else row[part]
                assert row == source["row"]
    unit = next(n for n in stories["c"]["fixture_citations"] if n.get("scale_error"))
    assert unit["stated_value_usd"] == unit["filed_value_usd"] * 1000
    assert unit["displayed_text"] == "$164,501 billion"
    assert stories["a"]["fixture_citations"][-1]["filed_value_usd"] == 102466000000
    assert [n["filed_value_usd"] for n in stories["b"]["fixture_citations"]] == [281724000000, 350018000000, 164501000000]


@pytest.mark.parametrize("tamper", ["fixture", "font", "unit", "uncited_number", "png", "manifest"])
def test_check_rejects_changed_sources_outputs_and_unit_arithmetic(tmp_path, monkeypatch, tamper):
    folder = isolate(tmp_path, monkeypatch)
    if tamper == "fixture":
        path = tmp_path / "tests/fixtures/sec-offline/companyfacts-CIK0001326801.json"
        path.write_bytes(path.read_bytes() + b"\n")
    elif tamper in {"unit", "uncited_number"}:
        path = folder / "stories.json"
        spec = json.loads(path.read_text())
        if tamper == "unit":
            spec["stories"][2]["numbers"][1]["stated_value_usd"] += 1
        else:
            spec["stories"][1]["text"] += "Uncited revenue: $999 billion.\n"
        path.write_text(json.dumps(spec))
    else:
        path = folder / {"font": assets.FONT, "png": "b.png", "manifest": "manifest.json"}[tamper]
        path.write_bytes(path.read_bytes() + b"tampered")
    with pytest.raises((ValueError, OSError)):
        assets.build(check=True)


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="Optional host FFmpeg encoder")
def test_retained_synthetic_wav_encodes_under_limits_and_reencodes_identically(tmp_path, monkeypatch):
    folder = isolate(tmp_path, monkeypatch)
    story = assets.load_stories()[0]
    source = folder / "narration/synthetic.wav"
    source.parent.mkdir(exist_ok=True)
    with wave.open(str(source), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(24000)
        stream.writeframes(struct.pack("<h", 1000) * (24000 * 21))
    info = {"text_sha256": assets.digest(story["text"].encode()), "source_wav": "narration/synthetic.wav",
            "source_sha256": assets.digest(source.read_bytes()), "outputs": {}}
    (folder / "narration/a.json").write_bytes(assets.encoded(info))
    assets.render_media([story])
    first = {p.name: p.read_bytes() for p in (folder / "a.mp3", folder / "a.mp4", folder / "narration/a.json")}
    rows = assets.build()
    for row in rows:
        if row["id"] in {"a-audio", "a-video"}:
            assert row["status"] == "ready" and 0 < row["duration_s"] <= 20 and row["size_bytes"] <= 2_000_000
    assets.render_media([story])
    assert first == {p.name: p.read_bytes() for p in (folder / "a.mp3", folder / "a.mp4", folder / "narration/a.json")}
    assets.build(check=True)


def test_recorder_redacts_echoed_password_in_json_and_malformed_bytes():
    secret = 'private-"雪-marker'
    for raw in (json.dumps({"nested": ["echo " + secret], "password": secret}).encode(),
                ("bad: " + secret).encode(), ("bad: " + json.dumps(secret)).encode()):
        result = recorder.sanitized(raw, secret)
        assert secret.encode() not in result
        assert json.dumps(secret)[1:-1].encode() not in result
        assert b"[REDACTED]" in result


@pytest.mark.parametrize("option", ["pending", "missing_password", "nan_budget"])
def test_recorder_rejects_unready_or_unconfigured_work_before_requests(tmp_path, monkeypatch, option):
    isolate(tmp_path, monkeypatch)
    monkeypatch.delenv("LIVE_CHECK_PASSWORD_FILE", raising=False)
    args = ["run_example_records.py", "--ids", "a-audio" if option == "pending" else "a-text", "--execute",
            "--max-spend-usd", "nan" if option == "nan_budget" else "3"]
    monkeypatch.setattr(sys, "argv", args)
    monkeypatch.setattr(recorder, "fetch", lambda *a: pytest.fail("unexpected API request"))
    with pytest.raises(SystemExit) as error:
        recorder.main()
    assert error.value.code == 2


@pytest.mark.parametrize("provider,model", [("fireworks", recorder.MODEL), ("baseten", "wrong-model")])
def test_recorder_never_publishes_a_different_provider_or_model(provider, model):
    asset = {"id": "b-text", "kind": "text", "story": "b"}
    value = {"mode": "live", "verdict": "supported", "input": {**asset, "example_id": "b-text", "text_read": "post"},
             "receipt": {"provider": provider, "model": model}, "claims": [], "evidence": [], "events": [], "corrections": []}
    assert not recorder.complete(value, asset)
