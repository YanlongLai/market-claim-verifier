"""Asset provenance, paper contrast and truthful publication metadata."""
import hashlib
import json
import re

import numpy as np
import pytest
from PIL import Image

from docs.scripts.build_site import ROOT, stamp_thread_position


ART = ROOT / "docs/site/img/polish"


def test_polish_exports_match_saved_exact_prompts_and_stay_within_the_shared_budget():
    manifest = json.loads((ART / "manifest.json").read_text())
    prompts = (ROOT / manifest["prompt_log"]).read_text()
    assert manifest["generator"] == "built-in image_gen"
    assert len(manifest["assets"]) == 11
    assert set(manifest["assets"]) == {path.name for path in ART.glob("*.webp")}
    assert not list(ART.glob("*.png")), "Production originals do not belong in the runtime asset set"
    assert sum(record["bytes"] for record in manifest["assets"].values()) == manifest["runtime_bytes"] <= 600_000
    for name, record in manifest["assets"].items():
        path = ART / name
        assert path.stat().st_size == record["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
        assert re.fullmatch(r"[a-f0-9]{64}", record["source_sha256"])
        assert record["prompt"] in prompts
        image = Image.open(path)
        assert list(image.size) == record["size"]
        if record["mode"] == "key":
            assert image.getchannel("A").getextrema() == (0, 255)
            pixels = np.asarray(image.convert("RGBA")).astype(int)
            pink = np.minimum(pixels[..., 0], pixels[..., 2]) - pixels[..., 1] > 35
            assert not np.any(pink & (pixels[..., 3] > 32)), name
    assert manifest["footer_reuse"] == "img/auditor/H/concern.webp"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_filing_paper_stays_warm_and_light_with_readable_ink_in_both_themes(theme):
    css = (ROOT / "docs/site/styles.css").read_text()
    palettes = [dict(re.findall(r"--([\w-]+):\s*([^;]+);", block))
                for block in re.findall(r":root\s*\{([^}]+)\}", css)]
    tokens = palettes[0] | (palettes[1] if theme == "dark" else {})

    def rgb(name):
        color = tokens[name]
        return [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]

    def luminance(channels):
        return sum(weight * (v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
                   for weight, v in zip((0.2126, 0.7152, 0.0722), channels))

    paper = rgb("filing-paper")
    assert paper[0] > paper[2] and luminance(paper) > 0.65
    if theme == "dark":
        assert 0.87 <= paper[0] / (int(palettes[0]["filing-paper"][1:3], 16) / 255) <= 0.89
    texture = Image.open(ART / "paper-grain.webp").convert("RGB")
    minimum = min(low for low, _ in texture.getextrema()) / 255
    backgrounds = [[channel * (0.5 + 0.5 * source) for channel in paper] for source in (minimum, 1)]
    for name in ("filing-ink", "filing-muted", "filing-stamp"):
        for ground in backgrounds:
            low, high = sorted((luminance(rgb(name)), luminance(ground)))
            assert (high + 0.05) / (low + 0.05) >= 4.5, (theme, name)
    assert "UNITED STATES SECURITIES AND EXCHANGE COMMISSION" in (ROOT / "docs/site/script.js").read_text()


def test_published_metadata_uses_existing_256px_avatars_and_recorded_input_kinds():
    cards = json.loads((ROOT / "docs/site/data/site.json").read_text())["stamp_cards"]
    for card in cards:
        assert card["input_kind"] in {"text", "audio", "screenshot"}
        assert ("input_media" in card) == (card["input_kind"] != "text")
        assert card["persona"]["fictional"] is True
        avatar = ROOT / "docs/site" / card["persona"]["avatar"]
        assert avatar.name.endswith("-256.webp") and Image.open(avatar).size == (256, 256)
        if "example_activity" in card:
            assert set(card["example_activity"]) == {"reply", "repost", "like", "views"}
        if card["source_kind"] == "thread":
            report = json.loads((ROOT / card["source_report"]).read_text())
            assert card["thread_index"] == stamp_thread_position(report["post"], card["quote"])
    bigtech = next(c for c in cards if c["id"] == "bigtech-thread-baseten-5")
    assert bigtech["thread_index"] == "5/5", "Six extracted claims came from five thread entries"
    html = (ROOT / "docs/site/index.html").read_text()
    for tag in re.findall(r"<img\b[^>]+>", html):
        assert 'loading="lazy"' in tag and 'decoding="async"' in tag


def test_dark_compare_paper_keeps_about_seventy_percent_brightness_and_a_warm_tone():
    css = (ROOT / "docs/site/styles.css").read_text()
    palettes = [dict(re.findall(r"--([\w-]+):\s*([^;]+);", block))
                for block in re.findall(r":root\s*\{([^}]+)\}", css)]
    tokens = palettes[0] | palettes[1]
    rgb = lambda name: [int(tokens[name][i:i + 2], 16) for i in (1, 3, 5)]
    paper, shade = rgb("filing-paper"), rgb("stamp-paper-dim")
    alpha = float(tokens["stamp-paper-dim-opacity"])
    unlit = [p * (1 - alpha) + s * alpha for p, s in zip(paper, shade)]
    brightness = lambda channels: sum(v * w for v, w in zip(channels, (0.2126, 0.7152, 0.0722)))
    assert 0.68 <= brightness(unlit) / brightness(paper) <= 0.76
    assert unlit[0] > unlit[1] > unlit[2]
    # A separate stage mask excludes the entire paper (including stack edges)
    # from the stage shade and atmosphere. Existing text masks expose lit rows.
    html = (ROOT / "docs/site/index.html").read_text()
    assert 'class="stamp-stage-hole-paper" fill="black"' in html
    assert 'class="stamp-stage-dim" mask="url(#stamp-stage-mask)"' in html
    assert 'class="stamp-fx-atmosphere" mask="url(#stamp-stage-mask)"' in html
    assert 'class="stamp-paper-dim"' in html
