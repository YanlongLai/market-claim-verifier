"""Reproducible assets and record provenance; never execute host model commands."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

from pypdf import PdfReader
import pytest

from scripts import build_examples as assets
from scripts import build_example_results as results
from scripts import run_example_records as recorder
from scripts import serve_site
from scripts.serve_site import output_path

ROOT = Path(__file__).resolve().parents[1]


def isolated(tmp_path, monkeypatch):
    for directory in ("docs/examples", "docs/site/data/examples"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    shutil.copyfile(ROOT / "docs/site/data/live-demo-post.json", tmp_path / "docs/site/data/live-demo-post.json")
    monkeypatch.setattr(assets, "ROOT", tmp_path)
    monkeypatch.setattr(assets, "EXAMPLES", tmp_path / "docs/examples")
    monkeypatch.setattr(results, "ROOT", tmp_path)
    monkeypatch.setattr(results, "OUTPUT", tmp_path / "docs/site/data/examples")
    monkeypatch.setattr(recorder, "ROOT", tmp_path)
    for name in ("server/live/server.py", "workers/live/src/live.py", "src/claimcheck/ingest_media.py",
                 "src/claimcheck/agent.py", "src/claimcheck/budget.py", "src/claimcheck/providers.py"):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return tmp_path


def test_five_example_manifest_hashes_native_pdf_and_root_relative_routes():
    rows = json.loads((ROOT / "docs/examples/manifest.json").read_text())
    assert [row["id"] for row in rows] == ["text", "image", "pdf", "audio", "video"]
    for row in rows:
        path = ROOT / "docs/examples" / row["file"]
        assert path.stat().st_size == row["size_bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
        assert set(row["contains"]) == {"en", "zh"}
        assert row["id"] == row["kind"]
        assert row["url"] == "/examples/" + row["file"]
        assert output_path(row["url"]) == path
        if row["status"] == "pending":
            assert row["file"].endswith(".pending.txt") and row["duration_s"] is None
        if row["kind"] == "video" and row["status"] == "ready":
            assert row["size_bytes"] <= 2_000_000 and 0 < row["duration_s"] <= 60
    post = json.loads((ROOT / "docs/site/data/live-demo-post.json").read_text())["input"]
    assert (ROOT / "docs/examples/post.txt").read_text() == post
    pdf = PdfReader(ROOT / "docs/examples/post.pdf")
    assert len(pdf.pages) == 1
    assert " ".join(pdf.pages[0].extract_text().split()) == " ".join(post.split())
    assert pdf.pages[0]["/Resources"]["/Font"]["/F1"]["/BaseFont"] == "/Times-Roman"


def test_asset_and_saved_envelope_builders_reproduce_every_byte_and_detect_staleness(tmp_path, monkeypatch):
    isolated(tmp_path, monkeypatch)
    before = {path.relative_to(tmp_path): path.read_bytes() for path in (tmp_path / "docs").rglob("*") if path.is_file()}
    for _ in range(2):
        assets.build()
        results.build()
        assets.build(check=True)
        results.build(check=True)
    assert before == {path.relative_to(tmp_path): path.read_bytes() for path in (tmp_path / "docs").rglob("*") if path.is_file()}
    (assets.EXAMPLES / "post.txt").write_text("wrong")
    with pytest.raises(ValueError, match="Stale example"):
        assets.build(check=True)


def test_preview_uses_published_examples_without_a_site_overlay(tmp_path, monkeypatch):
    published = tmp_path / "docs"
    for directory in ("examples", "site/examples"):
        (published / directory).mkdir(parents=True)
    (published / "examples/post.png").write_bytes(b"published image")
    (published / "site/examples/post.png").write_bytes(b"unpublished decoy")
    monkeypatch.setattr(serve_site, "ROOT", published)
    assert output_path("/examples/post.png").read_bytes() == b"published image"
    assert not output_path("/examples/missing.png").exists()


def test_pages_crawler_checks_even_unlinked_manifest_assets(tmp_path, monkeypatch, capsys):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    from scripts import check_site_routes as routes

    published = tmp_path / "docs"
    shutil.copytree(ROOT / "docs/examples", published / "examples")
    for name in ("index.html", "zh/index.html", "explorer/index.html", "explorer/index.zh.html", "llms.txt"):
        page = published / name
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text("No asset links.")
    monkeypatch.setattr(routes, "ROOT", published)
    monkeypatch.setattr(routes, "output_path", lambda url: published / url.lstrip("/"))
    assert not routes.crawl()
    capsys.readouterr()
    (published / "examples/post.png").unlink()
    assert routes.crawl()
    assert "MISSING /examples/post.png (from /examples/manifest.json)" in capsys.readouterr().out


def test_text_reuses_actual_envelope_and_other_saved_results_are_explicitly_pending():
    original = json.loads((ROOT / "docs/site/data/live-demo-post.json").read_text())
    saved = json.loads((ROOT / "docs/site/data/examples/text.json").read_text())
    if saved["recording"].get("type") == "reused_saved_text":
        assert saved["input"]["text_read"] == original.pop("input")
        for field in ("events", "claims", "evidence", "corrections", "cost_usd", "latency_ms", "sources"):
            assert saved[field] == original[field]
        assert saved["input"]["preprocessing"]["latency_ms"] is None
    index = json.loads((ROOT / "docs/site/data/examples/index.json").read_text())
    for row in index:
        if row["saved_result"]:
            assert output_path(row["saved_result"]).is_file()
        else:
            assert not (ROOT / f"docs/site/data/examples/{row['id']}.json").exists()


def test_host_recorder_requires_explicit_execution_before_any_request(tmp_path, monkeypatch):
    isolated(tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "argv", ["run_example_records.py", "--origin", "https://example.test", "--ids", "text", "--max-spend-usd", "3"])
    monkeypatch.setattr(recorder, "fetch", lambda *a: pytest.fail("host recording executed implicitly"))
    with pytest.raises(SystemExit) as error:
        recorder.main()
    assert error.value.code == 2
    assert not (tmp_path / "docs/evidence/example-records").exists()


def test_host_recorder_freezes_all_cases_retains_failure_and_does_not_store_password(tmp_path, monkeypatch):
    isolated(tmp_path, monkeypatch)
    output = tmp_path / "docs/evidence/example-records/offline-fixture"
    monkeypatch.setattr(sys, "argv", ["run_example_records.py", "--origin", "https://example.test", "--ids", "text", "image",
        "--max-spend-usd", "3", "--output", str(output), "--execute"])
    monkeypatch.setenv("LIVE_CHECK_PASSWORD", "recording-secret-marker")
    calls = []
    text = json.loads((results.OUTPUT / "text.json").read_text())
    text["mode"] = "live"
    def fetch(origin, path, body=None):
        calls.append((path, body))
        if path == "/api/budget":
            return 200, json.dumps({"day": "2026-11-03", "status": "ready", "daily_limit_usd": 3,
                                    "daily_remaining_usd": 3, "resets_at": "2099-11-04T00:00:00Z"}).encode()
        value = json.loads(body)
        assert (output / "plan.json").exists()
        assert value["password"] == "recording-secret-marker"
        return (200, json.dumps(text).encode()) if value["example_id"] == "text" else (504, b'{"error":"timeout","cost_is_bound":true}')
    monkeypatch.setattr(recorder, "fetch", fetch)
    with pytest.raises(SystemExit, match="incomplete/failed attempts: image"):
        recorder.main()
    assert len([call for call in calls if call[0] == "/api/check-example"]) == 2
    assert json.loads((output / "plan.json").read_text())["attempts_per_id"] == 1
    for example_id, status in (("text", 200), ("image", 504)):
        receipt = json.loads((output / example_id / "receipt.json").read_text())
        assert receipt["http_status"] == status
        assert receipt["response_sha256"] == hashlib.sha256((output / example_id / "response.json").read_bytes()).hexdigest()
    assert all("recording-secret-marker" not in path.read_text() for path in output.rglob("*") if path.is_file())
    before = (results.OUTPUT / "text.json").read_bytes()
    with pytest.raises(ValueError, match="Incomplete/mismatched"):
        results.build(records=output)
    assert (results.OUTPUT / "text.json").read_bytes() == before
    # Select a complete retained case only when explicitly requested, never a
    # fabricated image result or an implicit retry of the failed case.
    image = next(row for row in json.loads((assets.EXAMPLES / "manifest.json").read_text()) if row["id"] == "image")
    raw = json.dumps({**text, "input": {**text["input"], "example_id": "image", "kind": "image"}}).encode()
    retained = tmp_path / "docs/evidence/example-records/complete-offline-fixture/image"
    retained.mkdir(parents=True)
    (retained / "response.json").write_bytes(raw)
    (retained / "receipt.json").write_text(json.dumps({"http_status": 200, "attempts": 1, "example_id": "image",
        "response_sha256": hashlib.sha256(raw).hexdigest(), "asset_sha256": image["sha256"]}))
    results.build(records=retained.parent)
    results.build(check=True)
    saved = json.loads((results.OUTPUT / "image.json").read_text())
    assert saved["mode"] == "recorded" and saved["recording"]["attempts"] == 1
    (retained / "response.json").write_text("tampered")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        results.build(check=True)
