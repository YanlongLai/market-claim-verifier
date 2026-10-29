import json
import re
from pathlib import Path

import pytest

from docs.scripts.build_site import ROOT, stamp_cards


REPORT_DIR = Path("docs/evidence/posts-2026-10-28")
EXPECTED = {
    ("demo-thread-baseten", 1): "supported",
    ("demo-thread-baseten", 2): "supported",
    ("demo-thread-baseten", 3): "contradicted",
    ("demo-thread-baseten", 4): None,
    ("bigtech-thread-baseten", 3): "contradicted",
    ("bigtech-thread-baseten", 4): "supported",
    ("bigtech-thread-baseten", 5): None,
    ("tw-social-post-meta", 1): "supported",
    ("tw-social-post-meta", 3): "contradicted",
}


@pytest.fixture(scope="module")
def cards():
    return stamp_cards()


def report_claim(card):
    report = json.loads((ROOT / card["source_report"]).read_text(encoding="utf-8"))
    return next(claim for claim in report["claims"] if claim["index"] == card["claim_index"])


def test_stamp_cards_select_exactly_the_nine_brief_claims(cards):
    identities = [(Path(card["source_report"]).parent.name, card["claim_index"]) for card in cards]
    assert len(identities) == len(set(identities)) == 9
    assert set(identities) == set(EXPECTED)
    assert all(Path(card["source_report"]).parent.parent == REPORT_DIR for card in cards)


@pytest.mark.parametrize("identity,verdict", EXPECTED.items())
def test_stamp_verdict_and_provenance_match_the_source_report(cards, identity, verdict):
    report_id, claim_index = identity
    card = next(card for card in cards if card["source_report"] == f"{REPORT_DIR}/{report_id}/report.json" and card["claim_index"] == claim_index)
    claim = report_claim(card)
    assert card["verdict"] == claim.get("verdict") == verdict
    for key in ("ticker", "quote", "status", "kind", "summary"):
        assert card[key] == claim.get(key)
    if verdict in ("supported", "contradicted"):
        assert card["ticker"]
        assert (ROOT / card["source_report"]).is_file()


def test_stamp_loop_never_repeats_adjacent_verdicts_including_wraparound(cards):
    # At two-second intervals the opening three stamps teach all outcomes in 5s.
    assert {card["verdict"] for card in cards[:3]} == {"supported", "contradicted", None}
    for current, following in zip(cards, cards[1:] + cards[:1]):
        assert current["verdict"] != following["verdict"]


def test_stamp_links_and_evidence_chips_come_from_reports(cards):
    for card in cards:
        claim = report_claim(card)
        evidence = claim.get("evidence") or []
        urls = [item["filing_url"] for item in evidence if item.get("filing_url")]
        assert card["filing_url"] == (urls[0] if urls else None)
        if claim["status"] == "not_checked":
            assert card["kind"] in ("forecast", "opinion")
            assert card["evidence_label"] is None
        else:
            assert evidence
            assert card["evidence_label"].startswith("SEC 10-")
    # The derived Apple quarter has no filing link: preserve that absence instead
    # of inventing one. The UI can still link to its source report.
    apple_quarter = next(card for card in cards if card["id"] == "demo-thread-baseten-3")
    assert apple_quarter["filing_url"] is None
    assert "102.5 billion" in apple_quarter["summary"]


def test_stamp_cards_have_both_languages_and_preserve_original_chinese(cards):
    for card in cards:
        assert set(card["text"]) == {"en", "zh"}
        assert card["text"]["en"] and card["text"]["zh"]
        if "tw-social-post-meta" in card["source_report"]:
            assert card["text"]["zh"] == report_claim(card)["quote"]


def test_site_snapshot_contains_the_report_derived_stamp_cards(cards):
    snapshot = json.loads((ROOT / "docs/site/data/site.json").read_text(encoding="utf-8"))
    assert snapshot["stamp_cards"] == cards


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("verdict", ["true", "false", "unknown"])
def test_stamp_ink_has_at_least_three_to_one_contrast_on_paper(theme, verdict):
    css = (ROOT / "docs/site/styles.css").read_text(encoding="utf-8")
    roots = re.findall(r":root\s*\{([^}]+)\}", css)
    tokens = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6});", roots[theme == "dark"]))

    def luminance(color):
        channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))

    ink, paper = sorted((luminance(tokens[verdict]), luminance(tokens["stamp-paper"])))
    contrast = (paper + 0.05) / (ink + 0.05)
    assert contrast >= 3, f"{theme} {verdict}: {contrast:.2f}:1 on the actual paper token"
