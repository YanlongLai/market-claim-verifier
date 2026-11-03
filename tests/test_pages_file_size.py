from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_LIMIT = 25 * 1024 * 1024


def test_no_published_file_exceeds_cloudflare_pages_limit():
    too_big = [str(p.relative_to(ROOT)) for p in (ROOT / "docs").rglob("*")
               if p.is_file() and p.stat().st_size > PAGES_LIMIT]
    assert not too_big, f"move to evidence-archive/: {too_big}"
