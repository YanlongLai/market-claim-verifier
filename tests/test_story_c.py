"""Frozen production text/tool-result rechecks; no model calls or OCR/ASR."""
import copy
import json
from pathlib import Path

import pytest

from claimcheck.checks import evaluate_verdict
from claimcheck.correction import build_corrections
from claimcheck.post import screen_claims
from scripts.replay_story_c import proposals, replay, retained_runner

ROOT = Path(__file__).resolve().parents[1]
# Freeze the failed attempt even after the public examples are re-recorded.
RECORD = ROOT / "docs/evidence/example-records/20261104T083842.915381Z"
POST = (
    "A mixed market take\n\n"
    "Microsoft FY2025 revenue: $281.7 billion.\n\n"
    "Meta FY2024 revenue: $164,501 billion.\n\n"
    "My forecast: Microsoft will beat $281.7 billion next year.\n\n"
    "Microsoft's growth beat every rival this year.\n"
)


def envelope(kind="text"):
    return json.loads((RECORD / f"c-{kind}/response.json").read_text())


@pytest.mark.parametrize("kind", ["text", "image", "pdf"])
def test_saved_story_c_binds_each_fact_and_corrects_exact_thousandfold_error(kind):
    saved = envelope(kind)
    if kind == "text":
        assert saved["input"]["text_read"] == POST
    before = copy.deepcopy(saved)
    result = replay(saved)
    assert saved == before  # Never rewrite historical production evidence.
    assert result["verdict"] == "contradicted"
    msft, meta, forecast, opinion = result["checks"]
    assert [c["program_verdict"] for c in result["checks"]] == [
        "supported", "contradicted", "unchecked", "unchecked"]
    assert (msft["stated_value_used"], msft["actual_value"]) == (281.7e9, 281_724e6)
    assert (meta["stated_value_used"], meta["actual_value"]) == (164_501e9, 164_501e6)
    assert meta["stated_value_used"] / meta["actual_value"] == 1000
    assert "likely_unit_translation_error" in meta["flags"]
    assert all(c["reason"].endswith("unchecked_other_claim") for c in (forecast, opinion))
    for check in (msft, meta):
        context = check["claim_source_context"]
        assert "forecast" not in context["quote"]
        for left, right in context["spans"]:
            assert saved["input"]["text_read"][left:right] == context["quote"]
    edit, = result["corrections"]["edits"]
    assert (edit["original"], edit["replacement"]) == ("$164,501 billion", "$164.5 billion")
    assert saved["input"]["text_read"][edit["start"]:edit["end"]] == edit["original"]
    assert (edit["period"], edit["evidence_ids"]) == ("FY2024", ["E2"])
    assert edit["citations"][0]["url"] == saved["evidence"][1]["filing_url"]
    assert [c["reason_code"] for c in result["corrections"]["not_corrected"]] == [
        "supported", "not_judged", "not_judged"]


def test_literal_unit_error_overrides_model_normalized_value():
    saved = envelope()
    subs = proposals(saved)
    subs[1]["stated_value"] = 164_501e6  # A model must not silently fix the post's units.
    checks, verdict = evaluate_verdict(subs, retained_runner(saved))
    assert verdict == "contradicted"
    assert checks[1]["stated_value_used"] == 164_501e9
    assert checks[1]["stated_value_corrected"] is True
    edit, = build_corrections(POST, checks, saved["evidence"])["edits"]
    assert edit["replacement"] == "$164.5 billion"


@pytest.mark.parametrize("ids", [["E2"], [], ["E1", "E2"]])
def test_bound_source_literal_overrides_a_model_normalized_number_phrase(ids):
    saved = envelope()
    subs = proposals(saved)
    subs[1].update(stated_text="$164.5 billion", stated_value=164.5e9, evidence_ids=ids)
    checks, verdict = evaluate_verdict(subs, retained_runner(saved))
    assert verdict == "contradicted"
    assert checks[1]["stated_value_used"] == 164_501e9
    assert "stated_text_corrected_from_source" in checks[1]["flags"]
    edit, = build_corrections(POST, checks, saved["evidence"])["edits"]
    assert edit["replacement"] == "$164.5 billion"


@pytest.mark.parametrize("ids", [[], ["E1", "E2"]])
def test_evidence_recovery_keeps_the_bound_original_sentence(ids):
    saved = envelope()
    subs = proposals(saved)
    subs[1]["evidence_ids"] = ids
    checks, verdict = evaluate_verdict(subs, retained_runner(saved))
    assert verdict == "contradicted"
    meta = checks[1]
    assert meta["program_verdict"] == "contradicted"
    assert meta["evidence_binding"]["reason"] == "unique_match"
    assert meta["evidence_ids"] == ["E2"]
    assert meta["claim_source_context"]["quote"] == "Meta FY2024 revenue: $164,501 billion."


def test_saved_video_reuses_identical_frame_context_without_guessing_an_edit_span():
    saved = envelope("video")
    result = replay(saved)
    assert result["verdict"] == "contradicted"
    assert [c["program_verdict"] for c in result["checks"]] == [
        "supported", "contradicted", "unchecked", "unchecked"]
    for check in result["checks"][:2]:
        context = check["claim_source_context"]
        assert len(context["spans"]) == 3
        for left, right in context["spans"]:
            assert saved["input"]["text_read"][left:right] == context["quote"]
    # The combined transcript/frame text repeats the amount four times. Keep
    # the existing correction ambiguity guard rather than choosing one copy.
    assert result["corrections"]["edits"] == []
    assert result["corrections"]["not_corrected"][1]["reason_code"] == "ambiguous_span"


def test_exact_post_screen_keeps_facts_and_does_not_inherit_period_into_forecast():
    quotes = [
        "Microsoft FY2025 revenue: $281.7 billion.",
        "Meta FY2024 revenue: $164,501 billion.",
        "My forecast: Microsoft will beat $281.7 billion next year.",
        "Microsoft's growth beat every rival this year.",
    ]
    kinds = ["reported_fact", "reported_fact", "forecast", "opinion"]
    screened = screen_claims(POST, [
        {"quote": quote, "claim": sub["text"], "ticker": "META" if i == 1 else "MSFT", "kind": kind}
        for i, (quote, sub, kind) in enumerate(zip(quotes, proposals(envelope()), kinds))
    ])
    assert [c["status"] for c in screened] == ["to_verify", "to_verify", "not_checked", "rejected"]
    assert screened[2]["claim"] == "Microsoft will beat $281.7 billion next year"
    assert not any(c.get("event_period_context") or c.get("period_context") for c in screened)


@pytest.mark.parametrize("prefix", ["Guidance: ", "Non-GAAP: ", "Analysts forecast: "])
def test_source_sentence_qualifiers_survive_model_rewrites(prefix):
    saved = envelope()
    saved["input"]["text_read"] = POST.replace("Microsoft FY2025 revenue:", prefix + "Microsoft FY2025 revenue:")
    result = replay(saved)
    check = result["checks"][0]
    assert check["program_verdict"] == "insufficient_evidence"
    assert prefix in check["claim_source_context"]["quote"]


@pytest.mark.parametrize("text", [
    "Microsoft FY2024 revenue was $281.7 billion",  # Wrong period, not the Meta row.
    "Meta FY2025 revenue was $281.7 billion",       # Wrong issuer, not the Microsoft row.
    "Microsoft FY2025 net income was $281.7 billion",  # Wrong metric.
])
def test_rewrite_cannot_select_a_source_with_different_period_issuer_or_metric(text):
    saved = envelope()
    subs = proposals(saved)
    subs[0]["text"] = text
    checks, _ = evaluate_verdict(subs, retained_runner(saved))
    assert checks[0]["program_verdict"] == "insufficient_evidence"
    assert not checks[0].get("claim_source_context")


def test_conflicting_source_contexts_remain_ambiguous():
    saved = envelope()
    saved["input"]["text_read"] += "Guidance: Microsoft FY2025 revenue: $281.7 billion."
    result = replay(saved)
    assert result["checks"][0]["program_verdict"] == "insufficient_evidence"
    assert result["checks"][0]["reason"] == "ambiguous_release_claim_period"
    assert not result["checks"][0].get("claim_source_context")


@pytest.mark.parametrize("header", ["Guidance.", "Non-GAAP figures.", "FY2025 outlook."])
def test_unattached_release_header_cannot_be_discarded(header):
    saved = envelope()
    saved["input"]["text_read"] = header + "\n" + POST
    result = replay(saved)
    assert result["checks"][0]["program_verdict"] == "insufficient_evidence"
    assert not result["checks"][0].get("claim_source_context")
