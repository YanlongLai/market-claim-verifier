from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _source_hash(root: Path, relative: str) -> str:
    digest = hashlib.sha256()
    path = root / relative
    digest.update(relative.encode("utf-8"))
    digest.update(b"\0")
    digest.update(path.read_bytes())
    digest.update(b"\0")
    return digest.hexdigest()


def test_check_reports_changed_evidence_in_a_temp_copy(tmp_path: Path) -> None:
    script_source = Path(__file__).with_name("make_figures.py")
    script = tmp_path / "docs" / "scripts" / "make_figures.py"
    script.parent.mkdir(parents=True)
    shutil.copy2(script_source, script)

    source = tmp_path / "docs" / "evidence" / "trace.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"cost_usd": 0.01}\n', encoding="utf-8")
    output = tmp_path / "docs" / "figures" / "demo.png"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"not a real image, but an existing registered output")
    (tmp_path / "README.md").write_text("", encoding="utf-8")

    registry = {
        "version": 1,
        "figures": [
            {
                "id": "demo",
                "output": ["docs/figures/demo.png"],
                "kind": "chart",
                "generator": "make_demo",
                "data_sources": ["docs/evidence/*.json"],
                "readme_section": "Test",
                "generated_at": "2026-10-27T00:00:00Z",
                "inputs_sha256": _source_hash(tmp_path, "docs/evidence/trace.json"),
            }
        ],
    }
    registry_path = tmp_path / "docs" / "figures" / "figures.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    first = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert first.returncode == 0, first.stdout + first.stderr

    source.write_text('{"cost_usd": 0.02}\n', encoding="utf-8")
    second = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert second.returncode != 0
    assert "demo: inputs changed" in second.stdout
