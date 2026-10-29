from __future__ import annotations

import copy
import json
import math
import shutil
from pathlib import Path

import pytest

from claimcheck.checks import gap_assessment, program_check_gap
from claimcheck.post import refresh_evidence, with_report_gaps
from docs.scripts.build_site import ROOT, stamp_cards, stamp_gap_snapshot


REPORTS = ROOT / "docs/evidence/posts-2026-10-28"
pytestmark = pytest.mark.usefixtures("offline_stamp_facts")
GAP_FIELDS = {
    "severity", "score", "gap", "gap_kind", "direction_wrong",
    "filed_value_display", "stated_value_display",
}


@pytest.mark.parametrize(
    "difference,severity",
    [
        (0, "exact"), (1.9999, "minor"), (2, "moderate"),
        (2.0001, "moderate"), (9.9999, "moderate"), (10, "major"),
        (10.0001, "major"), (49.9999, "major"), (50, "major"), (50.0001, "severe"),
    ],
)
@pytest.mark.parametrize("actual", [100, -100])
def test_relative_band_edges_and_score(difference, severity, actual):
    result = gap_assessment(actual + difference, actual, "eq", 0, "value")
    assert result == {
        "gap_kind": "relative",
        "gap": pytest.approx(difference / 100),
        "direction_wrong": False,
        "severity": severity,
        "score": pytest.approx(max(0, 100 - 2 * difference)),
    }


@pytest.mark.parametrize(
    "difference,severity",
    [
        (0, "exact"), (0.9999, "minor"), (1, "moderate"),
        (1.0001, "moderate"), (4.9999, "moderate"), (5, "major"),
        (5.0001, "major"), (19.9999, "major"), (20, "major"), (20.0001, "severe"),
    ],
)
def test_percentage_point_band_edges_and_score(difference, severity):
    result = gap_assessment(100 + difference, 100, "eq", 0, "change_pct")
    assert result == {
        "gap_kind": "points",
        "gap": pytest.approx(difference),
        "direction_wrong": False,
        "severity": severity,
        "score": pytest.approx(max(0, 100 - 4 * difference)),
    }


@pytest.mark.parametrize("comparator", ["eq", "approx", "gt", "gte", "lt", "lte"])
@pytest.mark.parametrize("claim_type", ["value", "change_pct", "change_abs"])
def test_tolerance_boundary_and_comparators(comparator, claim_type):
    actual = 101 if comparator in {"lt", "lte"} else 99
    assert gap_assessment(100, actual, comparator, 1, claim_type)["severity"] == "exact"
    outside = gap_assessment(100, actual, comparator, 0.9999, claim_type)
    assert outside["gap"] > 0
    assert outside["severity"] != "exact"


@pytest.mark.parametrize("comparator", ["gt", "gte", "lt", "lte"])
def test_threshold_only_measures_the_unmet_side(comparator):
    actual = 110 if comparator in {"gt", "gte"} else 90
    result = gap_assessment(100, actual, comparator, 0, "value")
    assert result["gap"] == 0
    assert result["score"] == 100
    assert result["severity"] == "exact"
    # Equal numbers have no numeric gap, including for a strict comparator;
    # the existing verdict still decides whether the threshold itself is met.
    assert gap_assessment(100, 100, comparator, 0, "value")["gap"] == 0


@pytest.mark.parametrize("stated,actual", [(0.1, -0.1), (-0.1, 0.1), (1, -1), (10, -11)])
def test_opposite_directions_raise_severity_and_apply_penalty(stated, actual):
    result = gap_assessment(stated, actual, "eq", 0, "change_pct")
    assert result["direction_wrong"] is True
    assert result["severity"] == ("severe" if abs(stated - actual) > 20 else "major")
    assert result["score"] == pytest.approx(max(0, 100 - 4 * abs(stated - actual) - 30))


def test_tolerance_takes_precedence_over_direction_and_zero_has_no_direction():
    result = gap_assessment(0.1, -0.1, "eq", 0.5, "change_pct")
    assert (result["gap"], result["direction_wrong"], result["severity"], result["score"]) == (0, False, "exact", 100)
    assert gap_assessment(1, 0, "eq", 0, "change_pct")["direction_wrong"] is False
    assert gap_assessment(0, -1, "eq", 0, "change_pct")["direction_wrong"] is False
    assert gap_assessment(0, 0, "eq", 0, "value")["score"] == 100
    assert gap_assessment(1, 0, "eq", 0, "value") is None


@pytest.mark.parametrize("field,value", [(0, None), (1, None), (2, "invalid"), (3, None), (3, -1), (4, "other"), (0, True), (1, math.inf), (3, math.nan)])
def test_unassessable_inputs_have_no_score(field, value):
    arguments = [100, 90, "eq", 0, "value"]
    arguments[field] = value
    assert gap_assessment(*arguments) is None


@pytest.mark.parametrize(
    "report_id,index,severity,score,gap,gap_kind,direction_wrong,filed,stated",
    [
        ("demo-thread-baseten", 1, "exact", 100, 0, "relative", False, "$143.083B", "$143.100B"),
        ("demo-thread-baseten", 2, "exact", 100, 0, "relative", False, "$60.922B", "$60.900B"),
        ("bigtech-thread-baseten", 4, "exact", 100, 0, "relative", False, "$391.035B", "$391.000B"),
        ("tw-social-post-meta", 1, "exact", 100, 0, "relative", False, "$245.122B", "$245.100B"),
        ("demo-thread-baseten", 3, "severe", 0, 3.061835144926117, "relative", False, "$102.466B", "$416.200B"),
        ("bigtech-thread-baseten", 3, "major", 46.27720339850548, 5.930699150373631, "points", True, "-2.931%", "3.000%"),
        ("tw-social-post-meta", 3, "moderate", 87.50982767047024, 0.0624508616476488, "relative", False, "$47.061B", "$50.000B"),
    ],
)
def test_seven_expected_cards_from_real_saved_checks(report_id, index, severity, score, gap, gap_kind, direction_wrong, filed, stated):
    source = REPORTS / report_id / "report.json"
    original = json.loads(source.read_text(encoding="utf-8"))
    report = with_report_gaps(original, source.parent)
    claim = next(item for item in report["claims"] if item["index"] == index)
    card = next(item for item in stamp_cards() if item["id"] == f"{report_id}-{index}")
    assert GAP_FIELDS <= card.keys()
    assert card["severity"] == severity
    assert card["score"] == pytest.approx(score)
    assert card["gap"] == pytest.approx(gap)
    assert card["gap_kind"] == gap_kind
    assert card["direction_wrong"] is direction_wrong
    assert card["filed_value_display"] == filed
    assert card["stated_value_display"] == stated
    assert card["verdict"] == claim["verdict"]
    assert all("gap" in check for check in claim["program_checks"])
    assert any(check["gap"] and check["gap"]["score"] == card["score"] for check in claim["program_checks"])
    assert json.loads(source.read_text(encoding="utf-8")) == original


def test_cant_check_cards_have_null_gap_and_display_fields():
    unknown = [card for card in stamp_cards() if card["status"] != "verified"]
    assert len(unknown) == 2
    for card in unknown:
        assert all(card[field] is None for field in GAP_FIELDS)


def test_multi_check_card_uses_the_worst_assessment_and_matching_values():
    checks = [
        {"claim_type": "value", "stated_value_used": 100, "actual_value": 100, "comparator": "eq", "tolerance": 0, "program_verdict": "supported", "evidence_ids": ["E1"]},
        {"claim_type": "change_pct", "stated_value_used": 3, "actual_value": -3, "comparator": "eq", "tolerance": 0, "program_verdict": "contradicted", "evidence_ids": ["E2"]},
    ]
    for check in checks:
        check["gap"] = program_check_gap(check)
    card = stamp_gap_snapshot({"status": "verified", "verdict": "contradicted", "program_checks": checks})
    assert (card["severity"], card["gap_kind"], card["gap"], card["score"]) == ("major", "points", 6, 46)
    assert (card["filed_value_display"], card["stated_value_display"]) == ("-3.000%", "3.000%")


@pytest.mark.parametrize("report_dir", sorted(REPORTS.glob("*/report.json")), ids=lambda path: path.parent.name)
def test_refresh_saved_reports_offline_without_changing_existing_results(report_dir, tmp_path):
    destination = tmp_path / report_dir.parent.name
    shutil.copytree(report_dir.parent, destination)
    original = json.loads((destination / "report.json").read_text(encoding="utf-8"))
    refreshed = refresh_evidence(destination)
    assert json.loads((destination / "report.json").read_text(encoding="utf-8")) == refreshed
    assert (destination / "report.html").is_file()
    assert refreshed["verdicts"] == original["verdicts"]
    for before, after in zip(original["claims"], refreshed["claims"], strict=True):
        assert before.get("verdict") == after.get("verdict")
        for old, new in zip(before.get("program_checks", []), after.get("program_checks", []), strict=True):
            assert {key: new[key] for key in old} == old
            assert "gap" in new
            assert new["gap"] == program_check_gap(new)
    assert refresh_evidence(destination) == refreshed


def test_refresh_uses_saved_program_values_instead_of_model_numbers(tmp_path):
    report = {"claims": [{"program_checks": [{"stated_value_used": 3, "actual_value": -3, "comparator": "eq", "tolerance": 0, "program_verdict": "contradicted"}], "trace_path": "trace.json"}]}
    trace = {"final_verdict": {"sub_claims": [{"claim_type": "change_pct", "stated_value_used": 3, "actual_value": 3}]}}
    (tmp_path / "trace.json").write_text(json.dumps(trace), encoding="utf-8")
    original = copy.deepcopy(report)
    enriched = with_report_gaps(report, tmp_path)
    assert report == original
    gap = enriched["claims"][0]["program_checks"][0]["gap"]
    assert (gap["gap_kind"], gap["gap"], gap["direction_wrong"], gap["score"]) == ("points", 6, True, 46)


def test_unchecked_check_does_not_inherit_a_score_from_its_numeric_values():
    check = {"program_verdict": "unchecked", "claim_type": "value", "stated_value_used": 1, "actual_value": 1, "comparator": "eq", "tolerance": 0}
    assert program_check_gap(check) is None


def test_new_reports_with_claim_types_need_no_saved_trace(tmp_path):
    check = {"program_verdict": "supported", "claim_type": "value", "stated_value_used": 1, "actual_value": 1, "comparator": "eq", "tolerance": 0}
    report = with_report_gaps({"claims": [{"program_checks": [check]}]}, tmp_path)
    assert report["claims"][0]["program_checks"][0]["gap"]["score"] == 100
