"""Offline protections for phase-2 sampling, gold, privacy and shared budgets."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/real_world"))
from prepare_threads import sample
from build_threads_gold import build
from run_threads import public_media
from report_threads import summarize


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


def test_compound_false_support_keeps_true_components_separate_from_scope():
    cases = [{"id": "compound"}, {"id": "scope"}, {"id": "missing"}]
    gold = {"compound": {"gold_basis": "primary_release", "gold_verdict": "contradicted"},
            "scope": {"gold_basis": "scope_policy", "gold_verdict": "insufficient_evidence"},
            "missing": {"gold_basis": "primary_release", "gold_verdict": "supported"}}
    row = {"status": "completed", "verdict": "contradicted", "any_supported": True,
           "path": "post", "cost_usd": .1, "wall_seconds": 2, "verified_claims": 2, "proposed_count": 3}
    results = {"compound": {**row, "id": "compound"}, "scope": {**row, "id": "scope"}}
    block = summarize(cases, gold, results)
    assert block["primary_factual_accuracy"]["numerator"] == 1
    assert block["primary_factual_accuracy"]["denominator"] == 2
    assert block["primary_false_supported_rate"]["numerator"] == 0
    assert block["any_supported_component_on_negative_post_NOT_false_support"]["numerator"] == 1
    assert block["false_supported_vs_scope_policy"]["numerator"] == 1
    assert block["extraction_item_coverage"]["denominator"] == 3
    assert block["failure_items"] == 1
    results["compound"]["verdict"] = "supported"
    assert summarize(cases, gold, results)["primary_false_supported_rate"]["numerator"] == 1


def test_complete_budget_stop_report_keeps_every_pair_and_no_media_accuracy(tmp_path):
    import shutil
    from report_threads import build as report
    parent, out = tmp_path, tmp_path / "threads"
    out.mkdir()
    source = ROOT / "docs/evidence/real-world-2026-11-02"
    for name in ("REPORT.md", "metrics.json"):
        shutil.copyfile(source / name, parent / name)
    for name in ("claims.jsonl", "gold.jsonl", "media-gold.jsonl", "media-inputs.json"):
        shutil.copyfile(source / "threads" / name, out / name)
    cases = [json.loads(line) for line in (out / "claims.jsonl").read_text().splitlines()]
    def stopped(id, path):
        return {"id": id, "path": path, "status": "budget_stopped", "cost_usd": 0, "wall_seconds": 0, "model_calls": 0}
    for provider in ("baseten", "fireworks", "meta"):
        for path in ("agent", "post"):
            target = out / provider / path
            target.mkdir(parents=True)
            (target / "results.jsonl").write_text("".join(json.dumps(stopped(c["id"], path)) + "\n" for c in cases))
        target = out / "media" / provider
        target.mkdir(parents=True)
        (target / "results.jsonl").write_text("".join(json.dumps(stopped(id, "ingest")) + "\n" for id in ("M01", "M02")))
    (out / "ledger.jsonl").write_text("")
    (out / "RUN_END.json").write_text("{}")
    result = report(out)
    assert result["systems"]["baseten/agent"]["budget_stopped_items"] == 78
    assert result["systems"]["baseten/agent"]["primary_factual_accuracy"]["rate"] == 0
    assert result["systems"]["meta/ingest"]["primary_factual_accuracy"]["rate"] is None
    assert result["total_cost_usd"] == 0
    before = (parent / "REPORT.md").read_bytes()
    report(out)
    assert (parent / "REPORT.md").read_bytes() == before


def test_source_tier_correction_changes_only_metadata(tmp_path):
    from correct_threads_tiers import build as correct
    import shutil
    source = ROOT / "docs/evidence/real-world-2026-11-02/threads"
    shutil.copyfile(source / "gold.jsonl", tmp_path / "gold.jsonl")
    before = (tmp_path / "gold.jsonl").read_bytes()
    fixed = {r["id"]: r for r in correct(tmp_path)}
    assert fixed["T02"]["tier"] == ["L2", "L3"]
    assert fixed["T03"]["tier"] == ["L1", "L2"]
    assert fixed["T19"]["tier"] == ["L2", "L4"]
    assert (tmp_path / "gold.jsonl").read_bytes() == before
    def remove_metadata(x):
        if isinstance(x, list):
            return [remove_metadata(v) for v in x]
        if isinstance(x, dict):
            return {k: remove_metadata(v) for k, v in x.items() if k not in {"tier", "tier_policy"}}
        return x
    assert remove_metadata(list(fixed.values())) == remove_metadata(list(map(json.loads, before.decode().splitlines())))
