from claimcheck.ingest import coverage_summary, render_html


def test_empty_input_never_claims_complete_recall():
    summary = coverage_summary([])
    assert summary["full_content_recall"] is None
    assert summary["program_checked_claims"] == 0


def test_partial_and_insufficient_are_not_hidden():
    channels = [{"id": "text", "error": "budget exhausted", "claims": [
        {"kind": "reported_fact", "status": "completed", "program_checks": [True], "verdict": "insufficient_evidence"},
        {"kind": "reported_fact", "status": "failed"},
        {"kind": "reported_fact", "status": "rejected", "program_checks": [True]},
        {"kind": "opinion", "status": "skipped"},
    ]}]
    summary = coverage_summary(channels)
    assert summary["proposed_claims"] == 4
    assert summary["accepted_claims"] == 2
    assert summary["program_checked_claims"] == 1
    assert summary["accepted_without_program_checks"] == 1
    assert summary["rejected_claims"] == summary["failed_claims"] == 1
    assert summary["channels_with_errors"] == summary["insufficient_evidence_claims"] == 1
    assert summary["full_content_recall"] is None


def test_html_explains_unknown_denominator():
    html = render_html({"input": {"file": "sample.txt"}, "status": "completed", "channels": [], "errors": []})
    assert "Full-content recall: unknown" in html
    assert "0 program-checked" in html
    assert "does not mean supported" in html
