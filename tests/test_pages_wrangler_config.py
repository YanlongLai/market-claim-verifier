import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pages_wrangler_config_uses_only_pages_supported_keys():
    # Pages fails the whole build on Worker-only keys such as [observability].
    config = tomllib.loads((ROOT / "wrangler.toml").read_text())
    assert set(config) <= {"name", "pages_build_output_dir", "compatibility_date", "compatibility_flags", "vars"}
