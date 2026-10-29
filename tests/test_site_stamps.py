import json
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

import pytest

from docs.scripts.build_site import ROOT, first_reported_fact, stamp_cards, validate_stamp_post_date
from docs.scripts.filing_excerpts import SECFilingFetcher


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


def test_stamp_cards_keep_nine_checks_and_add_only_one_repost_and_one_article(cards):
    identities = [(Path(card["source_report"]).parent.name, card["claim_index"]) for card in cards]
    assert len(identities) == 11 and len(set(identities)) == 9
    assert set(identities) == set(EXPECTED)
    assert len({card["id"] for card in cards}) == 11
    assert len({card["check_id"] for card in cards}) == 9
    assert [card["source_kind"] for card in cards].count("repost") == 1
    assert [card["source_kind"] for card in cards].count("article") == 1
    assert all(Path(card["source_report"]).parent.parent == REPORT_DIR for card in cards)


def test_repost_and_news_reuse_the_original_claim_and_entire_assessment(cards):
    by_id = {card["id"]: card for card in cards}
    for variant in (by_id["market-recap-repost"], by_id["banana-news-article"]):
        original = by_id[variant["same_claim_as"]]
        for field in ("check_id", "quote", "source_report", "claim_index", "ticker", "status", "verdict",
                      "severity", "score", "gap", "gap_kind", "direction_wrong", "gap_relation", "excerpt",
                      "date_basis", "filed_value_display", "stated_value_display"):
            assert variant[field] == original[field], field
    assert by_id["market-recap-repost"]["reposted_from"] == "美股懶人包"
    assert by_id["market-recap-repost"]["text"] == by_id["tw-social-post-meta-3"]["text"]
    assert by_id["banana-news-article"]["text"] == {
        "en": "Amazon reports $143.1B in Q3 2023 revenue.", "zh": "亞馬遜 2023 年第 3 季營收達 1,431 億美元。",
    }


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
    # The first three reviews introduce every outcome; keep the wrap mixed too.
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


def test_every_checkable_card_has_a_real_matching_filing_row(cards):
    for card in cards:
        excerpt = card["excerpt"]
        if card["verdict"] not in {"supported", "contradicted"}:
            assert excerpt is None
            assert card["score"] is None
            continue
        assert excerpt["form"] in {"10-K", "10-Q"}
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", excerpt["filed"])
        assert excerpt["company"] == card["company"]
        assert urlparse(excerpt["primary_url"]).hostname in {"www.sec.gov", "data.sec.gov"}
        assert excerpt["fact"]["full_value"] == excerpt["source_evidence"]["value"]
        assert excerpt["value"] == excerpt["fact"]["raw_value"]
        if excerpt["type"] == "table":
            assert excerpt["row_label"] and excerpt["period_header"]
            assert float(excerpt["value"].replace(",", "")) * 10 ** excerpt["fact"]["scale"] == excerpt["fact"]["full_value"]
        else:
            assert len(excerpt["text"]) <= 220
            assert excerpt["value"] in excerpt["text"]


def test_apple_quarter_passage_labels_annual_row_and_preserves_both_sources(cards):
    card = next(card for card in cards if card["id"] == "demo-thread-baseten-3")
    excerpt = card["excerpt"]
    assert excerpt["form"] == "10-K"
    assert excerpt["value"] == "416,161"
    assert "2025" in excerpt["period_header"]
    derivation = excerpt["derivation"]
    annual, nine = derivation["full_year"], derivation["nine_months"]
    assert annual["value"] == 416161000000
    assert nine["value"] == 313695000000
    assert annual["value"] - nine["value"] == derivation["result"] == 102466000000
    assert annual["form"] == "10-K" and nine["form"] == "10-Q"
    assert annual["start"] == nine["start"] == "2024-09-29"
    assert annual["end"] == "2025-09-27" and nine["end"] == "2025-06-28"
    assert derivation["label"] == {"en": "Full year", "zh": "全年"}
    assert derivation["text"]["en"] == "Q4 = full year − nine months = $102.5B"
    for component in (annual, nine):
        assert component["accn"] and component["filed"]
        assert urlparse(component["filing_url"]).hostname == "www.sec.gov"


def test_cards_have_example_personas_requested_dates_and_real_company_periods(cards):
    from docs.scripts.build_site import STAMP_PERSONAS, STAMP_POST_DATES

    for card in cards:
        assert card["company"]
        source = card["id"] if card.get("same_claim_as") else Path(card["source_report"]).parent.name
        assert card["post_date"] == STAMP_POST_DATES[source]
        persona = card["persona"]
        assert persona["fictional"] is True
        assert persona["id"] == STAMP_PERSONAS[source]["id"]
        assert persona["followers"] == STAMP_PERSONAS[source]["followers"]
        assert set(persona["name"]) == set(persona["byline"]) == set(persona["follower_label"]) == {"en", "zh"}
        assert (ROOT / "docs/site" / persona["avatar"]).is_file()
        # Fictional post metadata must not mutate the real check reports.
        report = json.loads((ROOT / card["source_report"]).read_text())
        assert "post_date" not in report and "metadata" not in report
        if card["status"] == "verified":
            assert card["period"]["en"] and card["period"]["zh"]


def test_offline_rebuild_revalidates_dates_from_cached_sec_facts_without_network(monkeypatch):
    from docs.scripts import filing_excerpts

    def no_download(*_args):
        raise AssertionError("Offline stamp rebuild tried downloading a filing")

    monkeypatch.setattr(filing_excerpts, "urlopen", no_download)
    assert stamp_cards() == json.loads((ROOT / "docs/site/data/site.json").read_text())["stamp_cards"]


def test_date_basis_uses_the_earliest_sec_filing_for_every_concept_and_period(cards):
    for card in cards:
        basis = card["date_basis"]
        assert basis["method"] == "sec-companyfacts-first-filed"
        assert bool(basis["facts"]) == (card["status"] == "verified")
        for fact in basis["facts"]:
            data = json.loads((ROOT / f".cache/companyfacts-CIK{fact['cik']:010d}.json").read_text())
            values = data["facts"]["us-gaap"][fact["concept"]]["units"][fact["unit"]]
            dates = [item["filed"] for item in values if item.get("start") == fact["start"] and item["end"] == fact["end"]]
            assert fact["first_filed"] == min(dates)
            assert fact["first_filed"] <= card["post_date"] <= date.today().isoformat()
        assert basis["not_before"] == max((fact["first_filed"] for fact in basis["facts"]), default=None)


def test_date_basis_covers_both_growth_years_and_both_derived_quarter_components(cards):
    by_id = {card["id"]: card for card in cards}
    for identity in ("demo-thread-baseten-2", "bigtech-thread-baseten-3", "tw-social-post-meta-1"):
        assert len(by_id[identity]["date_basis"]["facts"]) == 2
    apple = by_id["demo-thread-baseten-3"]["date_basis"]
    assert {(fact["start"], fact["end"], fact["first_filed"]) for fact in apple["facts"]} == {
        ("2024-09-29", "2025-09-27", "2025-10-31"), ("2024-09-29", "2025-06-28", "2025-08-01"),
    }
    assert apple["not_before"] == "2025-10-31"


def test_first_reported_date_matches_period_concept_and_unit_even_when_a_later_filing_repeats_it():
    evidence = {"ticker": "KO", "concept": "Revenues", "unit": "USD", "start": "2024-01-01", "end": "2024-12-31"}
    def fact(filed, **fields):
        return {**evidence, "filed": filed, "accn": "first", "form": "10-K", "val": 47061000000, **fields}
    data = {"cik": 21344, "facts": {"us-gaap": {
        "Revenues": {"units": {"USD": [fact("2026-02-20"), fact("2025-02-20"),
                                        fact("2024-02-20", start="2023-01-01", end="2023-12-31")],
                                "shares": [fact("2023-02-20")]}},
        "NetIncomeLoss": {"units": {"USD": [fact("2022-02-20")]}},
    }}}
    assert first_reported_fact(evidence, data)["first_filed"] == "2025-02-20"
    with pytest.raises(ValueError, match="No SEC first-filing date"):
        first_reported_fact({**evidence, "start": "2024-10-01"}, data)


@pytest.mark.parametrize("posted,allowed", [("2025-02-19", False), ("2025-02-20", True), ("2025-02-24", True),
                                            ("2026-10-28", True), ("2026-10-29", False), ("20250224", False), ("bad", False)])
def test_post_dates_cannot_precede_any_fact_or_follow_today(posted, allowed):
    basis = {"not_before": "2025-02-20", "facts": [{"first_filed": "2024-07-30"}, {"first_filed": "2025-02-20"}]}
    if allowed:
        validate_stamp_post_date(posted, basis, today=date(2026, 10, 28))
    else:
        with pytest.raises(ValueError, match="post date"):
            validate_stamp_post_date(posted, basis, today=date(2026, 10, 28))


@pytest.mark.parametrize("source,posted", [("demo-thread-baseten", "2025-10-30"),
                                           ("banana-news-article", "2023-10-26"),
                                           ("market-recap-repost", "2025-02-19"),
                                           ("bigtech-thread-baseten", (date.today() + timedelta(days=1)).isoformat())])
def test_build_rejects_an_invalid_date_in_original_article_or_repost(monkeypatch, source, posted):
    from docs.scripts.build_site import STAMP_POST_DATES
    monkeypatch.setitem(STAMP_POST_DATES, source, posted)
    with pytest.raises(ValueError, match="post date"):
        stamp_cards()


def test_companyfacts_share_the_sec_only_cache_and_work_offline(tmp_path, monkeypatch):
    from docs.scripts import filing_excerpts
    def no_network(*_args):
        raise AssertionError("Cached companyfacts must not use the network")
    monkeypatch.setattr(filing_excerpts, "urlopen", no_network)
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({"cik": 21344, "facts": {}}))
    cache = tmp_path / "filings"
    assert SECFilingFetcher(cache, offline=True).load_companyfacts(21344, seed_cache=seed)["cik"] == 21344
    assert len(list(cache.glob("*.json"))) == 1
    seed.unlink()
    assert SECFilingFetcher(cache, offline=True).load_companyfacts(21344)["cik"] == 21344
    with pytest.raises(ValueError, match="No cached SEC filing"):
        SECFilingFetcher(cache, offline=True).load_companyfacts(320193)


def test_approved_severities_scores_and_threshold_gap(cards):
    expected = {"demo-thread-baseten-1": ("exact", 100), "demo-thread-baseten-2": ("exact", 100),
                "demo-thread-baseten-3": ("severe", 0), "bigtech-thread-baseten-3": ("major", 46),
                "tw-social-post-meta-1": ("exact", 100), "bigtech-thread-baseten-4": ("exact", 100),
                "tw-social-post-meta-3": ("moderate", 88)}
    for card in cards:
        if card["id"] in expected:
            assert (card["severity"], round(card["score"])) == expected[card["id"]]
    coca_cola = next(card for card in cards if card["ticker"] == "KO")
    assert coca_cola["gap_relation"] == "shortfall"


def test_archived_b_poses_and_original_v2_asset_budget_are_preserved():
    root = ROOT / "docs/site/img/auditor"
    all_poses = list((root / "B").glob("*.webp"))
    required = {"idle", "inspect", "present", "stamp"}
    optional = {"reach", "point", "think", "stamp-down", "approve", "concern", "shrug"}
    assert required <= {path.stem for path in all_poses} <= required | optional
    poses = [path for path in all_poses if path.stem in required]
    assert all(path.stat().st_size <= 120000 for path in poses)
    assert sum(path.stat().st_size for path in poses) <= 400000
    assert (root / "sheet-B.png").is_file()
    assert not (root / "A").exists() and not (root / "C").exists()
    assert not any(path.name in {"sheet-A.png", "sheet-C.png", "variant-A-preview.png", "variant-C-preview.png"} for path in root.rglob("*"))
    avatars = ROOT / "docs/site/img/personas"
    assert not list(avatars.glob("news-paper*"))
    assert {path.name for path in avatars.glob("*-128.webp")} == {
        f"{name}-128.webp" for name in ("retail-owl", "chart-raccoon", "lazy-cat", "repost-bird", "banana-news")
    }
    # Paper and ink textures predate v2; its new runtime artwork is B + avatars.
    new_assets = poses + list(avatars.glob("*-128.webp"))
    assert sum(path.stat().st_size for path in new_assets) <= 400000


@pytest.mark.parametrize("pose", ["idle", "inspect", "reach", "present", "point", "think", "stamp",
                                  "stamp-down", "approve", "concern", "shrug"])
def test_hover_pose_alpha_bounds_scale_and_anchors_match_the_runtime_manifest(pose):
    from PIL import Image

    root = ROOT / "docs/site/img/auditor/H"
    manifest = json.loads((root / "manifest.json").read_text())
    data = manifest["poses"][pose]
    path = root / data["file"]
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    assert list(image.size) == data["size"] == manifest["canonical_canvas"] == [704, 744]
    assert list(alpha.getbbox()) == data["bbox"]
    assert path.stat().st_size == data["bytes"] <= 70_000
    assert data["scale"] == manifest["shared_body_scale"] == 0.5
    assert data["nozzle_anchor"] == [352, manifest["nozzle_baseline_y"]] == [352, 520]
    assert alpha.getpixel(tuple(data["visor_anchor"])) > 200
    assert alpha.getpixel((352, 517)) > 32
    assert not alpha.crop((328, 524, 376, 744)).getbbox(), "Exhaust corridor contains no baked jet or stamp"
    assert all(not alpha.crop(box).getbbox() for box in [(0, 0, 704, 1), (0, 743, 704, 744),
                                                         (0, 0, 1, 744), (703, 0, 704, 744)])
    script = (ROOT / "docs/site/script.js").read_text()
    x, y = data["visor_anchor"]
    assert re.search(rf'(?:"{pose}"|\b{pose}): \{{ visor: \[{x}, {y}\], nozzle: \[352, 520\] \}}', script)


def test_hover_thrusters_are_separate_alpha_assets_with_a_reusable_prompt_and_composited_contact():
    from PIL import Image

    root = ROOT / "docs/site/img/auditor/H"
    manifest = json.loads((root / "manifest.json").read_text())
    frames = manifest["thruster"]["frames"]
    assert set(frames) == {f"thruster-{n}" for n in range(6)} | {"thruster-burst"}
    for name, data in frames.items():
        path = root / data["file"]
        image = Image.open(path).convert("RGBA")
        assert list(image.size) == [160, 160]
        assert list(image.getbbox()) == data["bbox"]
        assert image.getchannel("A").getextrema() == (0, 255)
        assert data["root_anchor"] == [80, 20]
        assert data["bytes"] == path.stat().st_size < 5_000
    assert manifest["thruster"]["burst_ms"] == 250
    assert manifest["thruster"]["burst_scale"] == 1.6
    assert manifest["runtime_bytes"] == sum(path.stat().st_size for path in root.glob("*.webp")) < 400_000
    assert Image.open(root / "contact.png").size == (1560, 1640)
    assert manifest["contact"]["strike_offsets_ms"] == [120, 160, 200, 240, 250, 420]
    prompt_log = (ROOT / "docs/prompts/site/auditor-robot.md").read_text()
    assert "v3 Hover — final" in prompt_log
    provenance = json.loads((root / "source/prompts.json").read_text())
    assert len(provenance["entries"]) == 16
    assert all(entry["prompt"] in prompt_log for entry in provenance["entries"])
    script = (ROOT / "docs/site/script.js").read_text()
    assert "img/auditor/B/" not in script
    assert "img/auditor/H/" in script


def test_cinematic_vfx_runtime_texture_budget_excludes_the_contact_sheet():
    names = ("beam-cone", "beam-pool", "dust-motes", "lens-flare", "impact-burst", "film-grain", "vignette")
    assets = [ROOT / "docs/site/img/fx" / f"{name}.webp" for name in names]
    assert all(asset.read_bytes()[:4] == b"RIFF" and asset.read_bytes()[8:12] == b"WEBP" for asset in assets)
    assert all(asset.stat().st_size < 60_000 for asset in assets)
    assert sum(asset.stat().st_size for asset in assets) <= 112_000
    assert (ROOT / "docs/site/img/fx/film-grain.webp").stat().st_size < 20_000


def test_scene_uses_cached_svg_geometry_compositor_transforms_and_fixed_panels():
    script = (ROOT / "docs/site/script.js").read_text()
    scene = script.split("  function createStampConveyor(cards) {", 1)[1].split("  function verdictClass", 1)[0]
    assert set(re.findall(r"\.style\.([a-zA-Z]+)\s*=", scene)) <= {"transform", "opacity"}
    css = (ROOT / "docs/site/styles.css").read_text()
    assert ".stamp-static-list.is-sr-only .stamp-card { width: 360px; }" in css
    assert re.search(r"\.stamp-mark\s*\{\s*position: relative;", css), "Ink bleed must stay inside the stamp"
    assert '.stamp-scene[data-animated="false"] .stamp-stage, .stamp-scene[data-animated="false"] .stamp-strip { display: none; }' in css
    assert 'PAPER_TRAVEL' not in scene and 'PAPER_RETURN' not in scene
    assert 'item.passage.body.style.transform' not in scene
    assert 'const origin = stage.getBoundingClientRect()' in scene
    before_measure, measure_and_after = scene.split('    function measure() {', 1)
    measure, after_measure = measure_and_after.split('    function tick(now) {', 1)
    for outside_measure in (before_measure, after_measure):
        assert 'getBoundingClientRect' not in outside_measure
        assert '.clientWidth' not in outside_measure
    assert 'Math.random' not in scene, "Light and dust must be seekable"
    assert 'sizeKey !== key' in measure, "Intrinsic maxima are cached across playback and seeks"
    assert 'filter:' not in css.split('.stamp-spotlight {', 1)[1].split('}', 1)[0]


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

    stamp_ink = {"true": "true", "false": "severity-severe", "unknown": "stamp-unknown"}[verdict]
    ink, paper = sorted((luminance(tokens[stamp_ink]), luminance(tokens["stamp-paper"])))
    contrast = (paper + 0.05) / (ink + 0.05)
    assert contrast >= 3, f"{theme} {verdict}: {contrast:.2f}:1 on the actual paper token"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_paper_text_and_severity_colours_keep_4_5_contrast_with_grain(theme):
    css = (ROOT / "docs/site/styles.css").read_text(encoding="utf-8")
    roots = re.findall(r":root\s*\{([^}]+)\}", css)
    palettes = [dict(re.findall(r"--([\w-]+):\s*([^;]+);", root)) for root in roots]
    tokens = palettes[0] | (palettes[1] if theme == "dark" else {})

    def rgb(color):
        return [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]

    def luminance(channels):
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
        return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))

    def contrast(first, second):
        low, high = sorted((luminance(first), luminance(second)))
        return (high + 0.05) / (low + 0.05)

    paper = rgb(tokens["stamp-paper"])
    if theme == "light":
        assert paper[0] > paper[2], "Light mode retains warm paper"
    else:
        assert paper[2] > paper[0], "Dark mode uses cool slate paper"
        assert luminance(paper) > luminance(rgb(tokens["bg"])), "The paper lifts slightly from the dark field"
    opacity = float(tokens["stamp-grain-opacity"])

    def grain(channel, source):
        if tokens["stamp-grain-blend"] == "multiply":
            blended = channel * source
        else:
            assert tokens["stamp-grain-blend"] == "soft-light"
            curve = ((16 * channel - 12) * channel + 4) * channel if channel <= 0.25 else channel ** 0.5
            blended = channel + (2 * source - 1) * (curve - channel)
        return channel * (1 - opacity) + blended * opacity

    # The bundled paper texture spans 212–255 across its RGB channels. Include
    # both conservative extremes so a flat-colour check cannot hide lost contrast.
    backgrounds = [[grain(channel, source) for channel in paper] for source in (212 / 255, 1)]
    text_tokens = ("ink", "stamp-muted", "stamp-unknown", "true", "severity-exact",
                   "severity-minor", "severity-moderate", "severity-major", "severity-severe")
    for name in text_tokens:
        ratio = min(contrast(rgb(tokens[name]), background) for background in backgrounds)
        assert ratio >= 4.5, f"{theme} {name}: {ratio:.2f}:1 with paper grain"
    assert min(contrast(rgb(tokens["stamp-meter-track"]), background) for background in backgrounds) >= 3
    amber = rgb(tokens["filing-fact"])
    for background in backgrounds:
        highlighted = [channel * 0.6 + accent * 0.4 for channel, accent in zip(background, amber)]
        assert contrast(rgb(tokens["ink"]), highlighted) >= 4.5, "Swept filing value stays readable"
    assert tokens["severity-minor"] == tokens["severity-moderate"], "Both middle severities use amber"


def test_page_sections_nav_and_shared_progress_headings_follow_the_v3_order():
    from html.parser import HTMLParser

    class Structure(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.sections = []
            self.nav = []
            self.parents = {}

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            parent_sections = [item[1].get("id") for item in self.stack if item[0] == "section"]
            if tag == "section" and not parent_sections and any(item[1].get("id") == "main" for item in self.stack):
                self.sections.append(attrs.get("id"))
            if attrs.get("id") in ("stamp-scene", "stamp-pause", "example-title"):
                self.parents[attrs["id"]] = list(self.stack)
            if tag == "a" and any(item[1].get("class") == "site-nav" for item in self.stack):
                self.nav.append(attrs["href"])
            if tag not in ("meta", "link", "img", "br", "hr", "input"):
                self.stack.append((tag, attrs))

        def handle_endtag(self, tag):
            assert self.stack and self.stack[-1][0] == tag, f"Unbalanced {tag}"
            self.stack.pop()

    html = (ROOT / "docs/site/index.html").read_text()
    structure = Structure()
    structure.feed(html)
    assert not structure.stack
    assert structure.sections == ["top", "how", "example", "results", "trust"]
    assert structure.nav == ["#how", "#example", "#results", "#trust"]
    assert any(attrs.get("id") == "top" for _, attrs in structure.parents["stamp-scene"])
    assert any(attrs.get("id") == "example" for _, attrs in structure.parents["example-title"])
    assert structure.parents["stamp-pause"][-1][1]["class"] == "stamp-strip"
    for step in range(1, 4):
        assert html.count(f'data-i18n="how.step{step}.title"') == 2
    assert 'class="stamp-queue"' not in html
    assert 'class="stamp-filing-box"' in html
