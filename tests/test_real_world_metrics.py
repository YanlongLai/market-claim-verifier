"""Protect evidence reporting against inflated accuracy and hidden failures."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("news_report", ROOT / "scripts/real_world/report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def test_unknown_truth_and_scope_skips_do_not_inflate_primary_accuracy():
    cases = [{"id": "positive"}, {"id": "scope"}, {"id": "review"}]
    gold = {"positive": {"gold_basis": "primary_release", "gold_verdict": "supported"},
            "scope": {"gold_basis": "scope_policy", "gold_verdict": "insufficient_evidence"},
            "review": {"gold_basis": "review_required", "gold_verdict": None}}
    results = {
        "positive": {"id": "positive", "path": "post", "status": "failed", "verdict": "supported", "cost_usd": 0.2, "wall_seconds": 5},
        "scope": {"id": "scope", "path": "post", "status": "completed", "verdict": None, "cost_usd": 0.1, "wall_seconds": 2},
        "review": {"id": "review", "path": "post", "status": "completed", "verdict": "supported", "cost_usd": 0.1, "wall_seconds": 3},
    }
    block = report.summarize(cases, gold, results)
    assert block["primary_factual_accuracy"]["numerator"] == 0
    assert block["primary_factual_accuracy"]["denominator"] == 1
    assert block["scope_expected_abstention_agreement"]["numerator"] == 1
    assert block["mixed_verdict_agreement_NOT_broad_factual_accuracy"]["denominator"] == 2
    assert block["review_unscored"] == 1
    assert block["primary_false_supported_rate"]["rate"] is None
    assert block["failure_items"] == 1
    assert block["items"] == 3
    assert abs(block["cost_usd"] - 0.4) < 1e-10
    assert block["latency_seconds"]["p95_nearest_rank"] == 5


def test_partial_post_support_remains_a_false_supported_scope_outcome():
    case = {"id": "unsupported"}
    gold = {"unsupported": {"gold_basis": "scope_policy", "gold_verdict": "insufficient_evidence"}}
    row = {"id": "unsupported", "status": "partial_failure", "verdict": "insufficient_evidence", "any_supported": True,
           "cost_usd": 0.25, "wall_seconds": 10, "verified_claims": 2, "counts": {"verified": 2, "failed": 1}}
    block = report.summarize([case], gold, {"unsupported": row})
    assert block["false_supported_vs_scope_policy"]["numerator"] == 1
    assert block["scope_expected_abstention_agreement"]["numerator"] == 0
    assert block["failure_items"] == 1
    assert block["mean_cost_per_verified_claim_or_agent_attempt_usd"] == 0.125


def test_missing_pairs_count_wrong_and_do_not_invent_latency_or_zero_false_support():
    cases = [{"id": "missing"}]
    gold = {"missing": {"gold_basis": "primary_release", "gold_verdict": "contradicted"}}
    block = report.summarize(cases, gold, {})
    assert block["primary_factual_accuracy"]["rate"] == 0
    assert block["failure_items"] == 1
    assert block["latency_seconds"]["n"] == 0
    assert report.wilson(0, 0) is None
    assert report.wilson(0, 4)[1] > 0.48
