"""Offline protections for phase-2 sampling, gold, privacy and shared budgets."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/real_world"))
from prepare_threads import sample
from build_threads_gold import build
from run_threads import public_media


def test_selection_is_order_independent_and_preserves_media_and_types():
    posts = [{"url": f"https://example.test/{i}", "text": f"dappgo\ntime\nT{i % 7}: earnings rose {i}%"} for i in range(70)]
    posts += [{"url": f"https://example.test/{p}", "text": "dappgo\ntime\nThe Magnificent Seven, page 1 of 4"}
              for p in ("De9xVYqmdev", "De9yipeGUJw")]
    selected = sample(posts)
    assert len(selected) == 30
    assert selected == sample(list(reversed(posts)))
    assert len({p["url"] for p in selected}) == 30
    assert all(any(p["url"].endswith(id) for p in selected) for id in ("De9xVYqmdev", "De9yipeGUJw"))


def test_gold_rebuild_preserves_scope_review_and_known_unit_period_errors(tmp_path):
    import shutil
    source = ROOT / "docs/evidence/real-world-2026-11-02/threads"
    shutil.copytree(source / "sources", tmp_path / "sources")
    shutil.copyfile(source / "claims.jsonl", tmp_path / "claims.jsonl")
    rows = {r["id"]: r for r in build(tmp_path)}
    assert rows["T02"]["gold_verdict"] == rows["T19"]["gold_verdict"] == "supported"
    assert all(rows[id]["gold_verdict"] == "contradicted" for id in ("T03", "T09", "T33"))
    assert rows["T10"]["gold_basis"] == rows["N07"]["gold_basis"] == "review_required"
    assert rows["N01"]["gold_basis"] == "scope_policy"
    assert (tmp_path / "gold.jsonl").read_bytes() == (source / "gold.jsonl").read_bytes()
    assert (tmp_path / "media-gold.jsonl").read_bytes() == (source / "media-gold.jsonl").read_bytes()


def test_actual_cli_transport_enforces_all_provider_caps_and_uses_one_ledger(tmp_path):
    ledger = tmp_path / "shared.jsonl"
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT / "scripts/real_world/threads_transport"), str(ROOT / "src")]),
               MCV_PHASE2_LEDGER=str(ledger), PYTHONDONTWRITEBYTECODE="1")
    code = """from claimcheck.budget import Ledger, BudgetExceeded
import sys
l = Ledger('wrong-ingest-ledger.jsonl', budget_usd=99, provider='baseten', provider_budgets={'meta':99})
assert str(l.path) == sys.argv[1]
assert all(l.budget_for_provider(p) == 8 for p in ('meta','baseten','fireworks'))
l.reserve('x',model='muse-spark-1.3',max_output_tokens=1800000,provider='meta')
try:
    l.reserve('x',model='muse-spark-1.3',max_output_tokens=100000,provider='meta')
except BudgetExceeded:
    pass
else:
    raise AssertionError('cross-route Meta cap was bypassed')
assert l.spent_for_provider('baseten') == 0
"""
    subprocess.run([sys.executable, "-c", code, str(ledger)], env=env, cwd=tmp_path, check=True)
    assert len(ledger.read_text().splitlines()) == 1


def test_public_media_projection_never_copies_verbatim_text(tmp_path):
    raw, public = tmp_path / "ignored", tmp_path / "public"
    (raw / "calls").mkdir(parents=True)
    secret_text = "a third-party headline that must stay local"
    (raw / "ingest.json").write_text(json.dumps({"status": "completed", "channels": [{"segments": [{"text": secret_text}],
        "claims": [{"quote": secret_text, "claim": secret_text, "status": "verified", "verdict": "insufficient_evidence"}]}]}))
    (raw / "calls/ocr.json").write_text(json.dumps({"response": secret_text, "attempts": [{"reservation": {"reservation_id": "r1", "provider": "meta"}, "cost_usd": 0.01}]}))
    public_media(raw, public, "meta", {"id": "M01", "sha256": "abc"},
                 {"command": ["claimcheck", "ingest"], "started_at": "a", "finished_at": "b", "exit_code": 0}, 1, {"meta": .01})
    assert all(secret_text not in p.read_text() for p in public.rglob("*.json"))
    assert json.loads((public / "requests.json").read_text())[0]["reservation"]["reservation_id"] == "r1"
