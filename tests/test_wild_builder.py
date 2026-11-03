"""Synthetic filesystem fixtures exercise the production evidence compiler."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from docs.scripts import build_wild as wild

FIXTURE = Path(__file__).parent / "fixtures/wild/probe.json"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n")


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


@pytest.fixture
def evidence(tmp_path):
    fixture = json.loads(FIXTURE.read_text())
    for phase, relative in (("news", wild.EVIDENCE), ("threads", wild.EVIDENCE / "threads")):
        part = fixture[phase]
        claims = {c["id"]: c for c in part["claims"]}
        for gold in part["gold"]:
            gold["claim_sha256"] = hashlib.sha256(claims[gold["id"]]["claim"].encode()).hexdigest()
        path = tmp_path / relative
        write_rows(path / "claims.jsonl", part["claims"])
        write_rows(path / "gold.jsonl", part["gold"])
        systems = {}
        for provider in wild.PROVIDERS:
            for route in wild.ROUTES:
                rows = deepcopy(part["results"])
                if phase == "threads" and provider == "fireworks" and route == "post":
                    rows[2]["status"] = "partial_failure"
                write_rows(path / provider / route / "results.jsonl", rows)
                # Recorded metrics accompany the raw fixture, just as in a run.
                counts = Counter((r["verdict"] or "skipped") if r["status"] == "completed" else r["status"] for r in rows)
                systems[f"{provider}/{route}"] = {"items": len(rows), "outcomes": dict(counts), "cost_usd": sum(r["cost_usd"] for r in rows)}
        write_json(path / "metrics.json", {"systems": systems, "total_cost_usd": sum(r["cost_usd"] for r in systems.values())})
        write_json(path / "RUN_END.json", {"finished_at": "2026-01-05T00:00:00Z"})
        if phase == "threads":
            write_rows(path / "gold-source-tiers-corrected.jsonl", part["gold"])
            write_json(path / "selection.json", {"own_selected": 2, "engagement_metrics": None})
    return tmp_path


def test_all_sources_failures_and_budget_stops_stay_in_denominators(evidence):
    data = wild.build(evidence)
    assert [s["items"] for s in data["sources"]] == [4, 2, 4]
    news = data["systems"]["baseten/agent"]["news"]
    assert news["items"] == 4
    assert news["attempted"] == 3
    assert news["outcomes"] == {"supported": 1, "contradicted": 0, "insufficient_evidence": 1, "skipped": 0, "failed": 1, "partial_failure": 0, "budget_stopped": 1}
    assert news["cost_per_item_usd"] == pytest.approx(.015)
    assert news["latency_seconds"] == {"n": 3, "mean": 10, "p50": 10, "p95": 20}
    assert news["outside_check"] == {"items": 2, "share": .5, "by_reason": {"taiwan": 1, "price_moves": 1, "private_companies": 0, "other": 0}}
    assert news["primary_truth"] == {"correct": 1, "items": 1}
    external = data["systems"]["baseten/agent"]["third_party_threads"]
    assert external["primary_truth"] == {"correct": 0, "items": 3}
    assert external["review_unscored"] == 1
    assert external["outcomes"]["skipped"] == 1
    assert data["systems"]["fireworks/post"]["third_party_threads"]["outcomes"]["partial_failure"] == 1


def test_independent_cards_do_not_cherry_pick_model_verdicts_or_guess_translation(evidence):
    data = wild.build(evidence)
    assert [card["id"] for card in data["cards"]] == ["T33", "T03", "T09"]
    card = data["cards"][0]
    assert card["verdict"] == "contradicted"  # The fixture model wrongly supported it.
    assert card["handle"] == "@fixture"
    assert card["components"][0]["filed"] == "50000000000"
    assert card["auto_translated"] is True
    assert not any(c["likely_unit_translation_error"] for c in data["cards"])
    assert "T10" not in {c["id"] for c in data["cards"]}
    assert all("claim" not in card for card in data["cards"])
    assert data["fixcheck"] is None
    assert all(len(digest) == 64 for digest in data["evidence_sha256"].values())


def test_deterministic_bytes_and_check_mode(evidence):
    assert wild.serialize(wild.build(evidence)) == wild.serialize(wild.build(evidence))
    command = [sys.executable, str(wild.ROOT / "docs/scripts/build_wild.py"), "--root", str(evidence)]
    assert subprocess.run(command, capture_output=True).returncode == 0
    assert subprocess.run(command + ["--check"], capture_output=True).returncode == 0
    (evidence / wild.OUTPUT).write_text("stale")
    result = subprocess.run(command + ["--check"], text=True, capture_output=True)
    assert result.returncode == 1
    assert "Stale or missing output" in result.stderr


@pytest.mark.parametrize("relative", ["claims.jsonl", "threads/metrics.json", "threads/RUN_END.json", "threads/gold-source-tiers-corrected.jsonl", "fireworks/post/results.jsonl"])
def test_missing_required_evidence_is_an_error_without_overwriting_saved_output(evidence, relative):
    output = evidence / wild.OUTPUT
    output.parent.mkdir(parents=True)
    output.write_bytes(b"prior saved result")
    (evidence / wild.EVIDENCE / relative).unlink()
    result = subprocess.run([sys.executable, str(wild.ROOT / "docs/scripts/build_wild.py"), "--root", str(evidence)], text=True, capture_output=True)
    assert result.returncode == 1
    assert "Required evidence missing" in result.stderr
    assert relative in result.stderr
    assert output.read_bytes() == b"prior saved result"


@pytest.mark.parametrize("mutation,match", [("duplicate", "Duplicate ids"), ("missing", "Incomplete result inventory"), ("hash", "hash mismatch"), ("metrics", "Metrics cost mismatch"), ("tier_verdict", "changed truth label"), ("unsafe_source", "Filing source must be SEC"), ("translation", "Translation label lacks evidence")])
def test_rejects_inconsistent_or_unsafe_evidence(evidence, mutation, match):
    base = evidence / wild.EVIDENCE
    if mutation in {"duplicate", "missing"}:
        path = base / "baseten/agent/results.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        write_rows(path, rows + [rows[0]] if mutation == "duplicate" else rows[:-1])
    elif mutation == "hash":
        path = base / "claims.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["claim"] += " changed"
        write_rows(path, rows)
    elif mutation == "metrics":
        path = base / "metrics.json"
        data = json.loads(path.read_text())
        data["systems"]["baseten/agent"]["cost_usd"] = 42
        write_json(path, data)
    else:
        path = base / "threads/gold-source-tiers-corrected.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if mutation == "tier_verdict": rows[2]["gold_verdict"] = "supported"
        if mutation == "unsafe_source": rows[2]["components"][0]["source"]["url"] = "https://example.com/fake-filing"
        if mutation == "translation": rows[2]["likely_unit_translation_error"] = True
        write_rows(path, rows)
    with pytest.raises(wild.EvidenceError, match=match):
        wild.build(evidence)


def test_optional_fixcheck_is_required_to_be_complete_and_kept_separate(evidence):
    path = evidence / wild.FIXCHECK
    path.mkdir()
    with pytest.raises(wild.EvidenceError, match="REPORT.md"):
        wild.build(evidence)
    write_json(path / "case.json", {"id": "T33", "before": "supported", "after": "contradicted"})
    summary = {"kind": "posthoc_fixcheck", "comparisons": [{"id": "T33", "description": {"en": "Fixture unit correction", "zh": "測試單位修正"}, "before": {"en": "Supported", "zh": "支持"}, "after": {"en": "Contradicted", "zh": "不符"}, "evidence_path": (wild.FIXCHECK / "case.json").as_posix()}]}
    write_json(path / "summary.json", summary)
    data = wild.build(evidence)
    assert data["fixcheck"] == summary
    assert data["systems"]["baseten/agent"]["third_party_threads"]["outcomes"]["supported"] == 1
    assert (wild.FIXCHECK / "case.json").as_posix() in data["evidence_sha256"]


def test_optional_fixcheck_can_retain_explicit_report_comparisons(evidence):
    path = evidence / wild.FIXCHECK / "REPORT.md"
    path.parent.mkdir()
    path.write_text("# Post-hoc fix recheck\n\nNo complete comparison yet.\n")
    with pytest.raises(wild.EvidenceError, match="No explicit Before/After table"):
        wild.build(evidence)
    path.write_text("# Post-hoc fix recheck\n\n| Case | Claim | Before | After |\n|---|---|---|---|\n| T33 | Private body must not be copied | supported | contradicted |\n")
    data = wild.build(evidence)
    assert data["fixcheck"]["report_excerpt"] is True
    comparison = data["fixcheck"]["comparisons"][0]
    assert comparison["before"] == "supported"
    assert comparison["after"] == "contradicted"
    assert comparison["description"] == {"en": "T33", "zh": "T33"}
    assert "Private body" not in json.dumps(data)
    assert (wild.FIXCHECK / "REPORT.md").as_posix() in data["evidence_sha256"]
