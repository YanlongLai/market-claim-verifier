import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_site_asset_links_carry_current_content_hash():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/stamp_site_assets.py"), "--check"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout
