"""Day-4 site cards must be projections of saved runs and hash-checked inputs."""
import copy
import hashlib

import pytest

from docs.scripts import build_site as site


pytestmark = pytest.mark.usefixtures("offline_stamp_facts")


@pytest.fixture
def cards():
    return {card["id"]: card for card in site.stamp_cards()}


def test_day4_cards_are_in_the_first_minute_and_keep_the_original_opening(cards):
    assert len(cards) == 15
    sequence = list(cards.values())
    assert [card["id"] for card in sequence[3:7]] == [
        "l4-01", "input-audio-two-voices-2", "l4-27", "input-screenshot-2",
    ]
    assert len({card["check_id"] for card in sequence}) == 13
    assert [card["verdict"] for card in sequence[:3]] == ["supported", "contradicted", None]
    for card, following in zip(sequence, sequence[1:] + sequence[:1]):
        assert card["verdict"] != following["verdict"]


@pytest.mark.parametrize("claim_id", ["L4-01", "L4-27"])
def test_release_paper_retains_exact_quote_highlight_period_and_furnished_provenance(cards, claim_id):
    card = cards[claim_id.lower()]
    claim, trace, check, evidence, doc = site.recorded_release(claim_id)
    excerpt = card["excerpt"]
    assert card["verdict"] == check["program_verdict"] == "supported"
    assert card["quote"] == claim["claim"] == trace["claim"]
    assert excerpt["type"] == "release" and excerpt["form"] == "8-K Ex 99.1"
    assert excerpt["text"] == evidence["quote"] == doc.text[evidence["start"]:evidence["end"]]
    for start, end in excerpt["highlight_ranges"]:
        assert excerpt["text"][start:end] == evidence["literal"]
    assert evidence["provenance"]["furnished"] and evidence["provenance"]["unaudited"]
    assert evidence["provenance"]["tier"] == "L4" and not evidence["provenance"]["audited"]
    assert excerpt["filed"] <= card["post_date"]
    assert card["persona"]["fictional"]
    site.validate_stamp_filing(card)


def test_guidance_shows_both_recorded_endpoints_without_a_scalar_score(cards):
    guidance = cards["l4-01"]
    assert guidance["score"] is None and guidance["gap"] is None
    assert guidance["filed_value_display"] == guidance["stated_value_display"] == "$47.500B–$50.500B"
    assert cards["l4-27"]["filed_value_display"] == "$5.310"


@pytest.mark.parametrize("claim_id", ["L4-01", "L4-27"])
@pytest.mark.parametrize("change", ["date", "number", "quote"])
def test_release_validation_rejects_display_date_number_or_quote_drift(cards, claim_id, change):
    card = copy.deepcopy(cards[claim_id.lower()])
    if change == "date":
        card["post_date"] = "2025-01-01"
    elif change == "number":
        card["excerpt"]["source_evidence"]["low"] += 1
    else:
        card["excerpt"]["text"] += " altered"
    with pytest.raises(ValueError):
        site.validate_stamp_filing(card)


def test_release_builder_rejects_changed_recorded_numbers_instead_of_copying_them(monkeypatch):
    original = site.read_json

    def changed(path):
        data = original(path)
        if path.name == "L4-01.json":
            data["program_checks"][0]["release_evidence"]["low"] += 1
        return data

    monkeypatch.setattr(site, "read_json", changed)
    with pytest.raises(ValueError, match="source span / numbers mismatch"):
        site.release_stamp_card("L4-01")


@pytest.mark.parametrize("run", ["audio-two-voices", "screenshot"])
def test_media_error_is_the_recorded_contradiction_with_first_filed_eps(cards, run):
    card = cards[f"input-{run}-2"]
    ingest = site.read_json(site.ROOT / card["source_ingest"])
    recorded = ingest["channels"][0]["claims"][1]
    check = recorded["program_checks"][0]
    assert card["quote"] == recorded["quote"]
    assert card["verdict"] == recorded["verdict"] == check["program_verdict"] == "contradicted"
    assert check["stated_value_used"] == 1.67 and check["actual_value"] == 1.57
    assert card["stated_value_display"] == "$1.670" and card["filed_value_display"] == "$1.570"
    assert card["excerpt"]["filed"] == "2025-08-01" <= card["post_date"]
    assert card["excerpt"]["fact"]["full_value"] == 1.57
    media = card["input_media"]
    assert hashlib.sha256((site.ROOT / media["source_fixture"]).read_bytes()).hexdigest() == media["sha256"]
    assert "Self-made synthetic test media" in media["disclosure"]["en"]
    site.validate_stamp_filing(card)


def test_audio_waveform_timing_and_unverified_label_come_from_the_actual_turn(cards):
    media = cards["input-audio-two-voices-2"]["input_media"]
    assert (media["timestamp"], media["end_timestamp"], media["speaker"], media["turn_id"]) == ("00:14.06", "00:25.82", "A", "turn-2")
    assert media["transcript"]["en"] == "Apple reported diluted earnings per share of $1.67 for fiscal 2025 third quarter"
    assert media["waveform"] == site.turn_waveform(site.ROOT / media["source_fixture"], 14060, 25820)
    assert len(set(media["waveform"])) > 10 and all(0 <= peak <= 1 for peak in media["waveform"])
    assert "both synthetic voices labeled A" in media["limit"]["en"]


def test_screenshot_is_the_exact_recorded_image_and_not_a_styled_reconstruction(cards):
    media = cards["input-screenshot-2"]["input_media"]
    assert (site.ROOT / "docs/site" / media["thumbnail"]).read_bytes() == (site.ROOT / media["source_fixture"]).read_bytes()
    assert "timestamp" not in media and "speaker" not in media


def test_capabilities_follow_how_and_link_to_saved_reports_with_static_replays():
    html = (site.ROOT / "docs/site/index.html").read_text()
    assert html.index('id="how"') < html.index('id="capabilities"') < html.index('id="example"')
    for report in ["eval-v2-2026-10-27/REPORT.md", "eval-l4-2026-10-29/ANALYSIS.md", "multimodal-2026-10-29/REPORT.md"]:
        assert f'href="../evidence/{report}"' in html
        assert (site.ROOT / "docs/evidence" / report).is_file()
    for seconds in (25.5, 33.5, 49.5):
        assert f'href="?stamp-t={seconds}#top"' in html
    script = (site.ROOT / "docs/site/script.js").read_text()
    assert "Known period-loss error in video" in script and "影片已知有期間遺失錯誤" in script
