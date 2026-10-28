"""Versioned prompt registry and export/synchronization helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


PROMPT_FILE_NAMES = {
    "agent_tool_loop_instructions": "agent-tool-loop-instructions.md",
    "agent_final_verdict_prompt": "agent-final-verdict-prompt.md",
    "baseten_tool_loop_instructions": "baseten-tool-loop-instructions.md",
    "baseten_final_verdict_prompt": "baseten-final-verdict-prompt.md",
    "baseten_repair_prompt": "baseten-repair-prompt.md",
    "baseten_single_shot_instructions": "baseten-single-shot-instructions.md",
    "fireworks_tool_loop_instructions": "fireworks-tool-loop-instructions.md",
    "fireworks_final_verdict_prompt": "fireworks-final-verdict-prompt.md",
    "fireworks_repair_prompt": "fireworks-repair-prompt.md",
    "fireworks_single_shot_instructions": "fireworks-single-shot-instructions.md",
    "verdict_json_schema": "verdict-json-schema.md",
    "tool_schemas": "tool-schemas.md",
    "single_shot_instructions": "single-shot-instructions.md",
}

PROMPT_LABELS = {
    "agent_tool_loop_instructions": "Agent tool-loop instructions",
    "agent_final_verdict_prompt": "Agent final-verdict prompt",
    "baseten_tool_loop_instructions": "Baseten tool-loop instructions",
    "baseten_final_verdict_prompt": "Baseten final-verdict JSON prompt",
    "baseten_repair_prompt": "Baseten verdict repair prompt",
    "baseten_single_shot_instructions": "Baseten single-shot instructions",
    "fireworks_tool_loop_instructions": "Fireworks tool-loop instructions",
    "fireworks_final_verdict_prompt": "Fireworks final-verdict JSON prompt",
    "fireworks_repair_prompt": "Fireworks verdict repair prompt",
    "fireworks_single_shot_instructions": "Fireworks single-shot instructions",
    "verdict_json_schema": "Verdict JSON schema",
    "tool_schemas": "Tool schemas",
    "single_shot_instructions": "Single-shot instructions",
}


def _json_text(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prompt_registry() -> dict[str, dict[str, str]]:
    """Return the exact source texts used to construct evaluation requests.

    Imports are intentionally lazy: the agent and evaluator both import this
    module, while the registry is only needed after their prompt constants have
    been defined.
    """

    from .agent import AGENT_FINAL_VERDICT_PROMPT, SYSTEM_INSTRUCTIONS, VERDICT_SCHEMA
    from .evaluate import SINGLE_SHOT_INSTRUCTIONS
    from .providers import (
        baseten_final_verdict_prompt,
        baseten_repair_prompt,
        baseten_single_shot_instructions,
        baseten_tool_loop_instructions,
        fireworks_final_verdict_prompt,
        fireworks_repair_prompt,
        fireworks_single_shot_instructions,
        fireworks_tool_loop_instructions,
    )
    from .tools import TOOL_DEFINITIONS

    texts = {
        "agent_tool_loop_instructions": SYSTEM_INSTRUCTIONS,
        "agent_final_verdict_prompt": AGENT_FINAL_VERDICT_PROMPT,
        "baseten_tool_loop_instructions": baseten_tool_loop_instructions(),
        "baseten_final_verdict_prompt": baseten_final_verdict_prompt(),
        "baseten_repair_prompt": baseten_repair_prompt(),
        "baseten_single_shot_instructions": baseten_single_shot_instructions("{today}"),
        "fireworks_tool_loop_instructions": fireworks_tool_loop_instructions(),
        "fireworks_final_verdict_prompt": fireworks_final_verdict_prompt(),
        "fireworks_repair_prompt": fireworks_repair_prompt(),
        "fireworks_single_shot_instructions": fireworks_single_shot_instructions("{today}"),
        "verdict_json_schema": _json_text(VERDICT_SCHEMA),
        "tool_schemas": _json_text(TOOL_DEFINITIONS),
        "single_shot_instructions": SINGLE_SHOT_INSTRUCTIONS,
    }
    return {
        name: {
            "text": text,
            "sha256": _sha256(text),
            "file": PROMPT_FILE_NAMES[name],
        }
        for name, text in texts.items()
    }


def prompt_versions_for(system: str) -> dict[str, str]:
    """Return prompt hashes for the prompts a system can send."""

    registry = prompt_registry()
    if system in {"single_shot", "single_shot@meta"}:
        names = ("single_shot_instructions", "verdict_json_schema")
    elif system in {"agent", "agent@meta"}:
        names = (
            "agent_tool_loop_instructions",
            "agent_final_verdict_prompt",
            "verdict_json_schema",
            "tool_schemas",
        )
    elif system == "single_shot@baseten":
        names = ("baseten_single_shot_instructions", "verdict_json_schema")
    elif system == "agent@baseten":
        names = (
            "baseten_tool_loop_instructions",
            "baseten_final_verdict_prompt",
            "baseten_repair_prompt",
            "verdict_json_schema",
            "tool_schemas",
        )
    elif system == "single_shot@fireworks":
        names = ("fireworks_single_shot_instructions", "verdict_json_schema")
    elif system == "agent@fireworks":
        names = (
            "fireworks_tool_loop_instructions",
            "fireworks_final_verdict_prompt",
            "fireworks_repair_prompt",
            "verdict_json_schema",
            "tool_schemas",
        )
    else:
        names = ()
    return {name: registry[name]["sha256"] for name in names}


def _markdown_for_prompt(name: str, entry: Mapping[str, str]) -> str:
    text = entry["text"]
    language = "json" if name in {"verdict_json_schema", "tool_schemas"} else "text"
    return (
        f"# {PROMPT_LABELS[name]}\n\n"
        f"<!-- sha256: {entry['sha256']} -->\n\n"
        f"Generated by `python -m claimcheck prompts export`.\n\n"
        f"```{language}\n{text}\n```\n"
    )


def prompt_file_contents() -> dict[str, str]:
    registry = prompt_registry()
    return {
        entry["file"]: _markdown_for_prompt(name, entry)
        for name, entry in registry.items()
    }


def prompts_root() -> Path:
    return Path(__file__).resolve().parents[2] / "prompts"


def prompt_files_in_sync(root: str | Path | None = None) -> tuple[bool, list[str]]:
    destination = Path(root) if root is not None else prompts_root()
    expected = prompt_file_contents()
    actual_names = {
        path.name
        for path in destination.glob("*.md")
    } if destination.is_dir() else set()
    expected_names = set(expected)
    problems = sorted(
        name
        for name in expected_names | actual_names
        if not (destination / name).is_file()
        or (destination / name).read_text(encoding="utf-8") != expected.get(name)
    )
    return not problems, problems


def export_prompt_files(root: str | Path | None = None) -> list[Path]:
    destination = Path(root) if root is not None else prompts_root()
    destination.mkdir(parents=True, exist_ok=True)
    contents = prompt_file_contents()
    for filename, content in contents.items():
        (destination / filename).write_text(content, encoding="utf-8")
    for path in destination.glob("*.md"):
        if path.name not in contents:
            path.unlink()
    return [destination / filename for filename in sorted(contents)]


__all__ = [
    "PROMPT_FILE_NAMES",
    "export_prompt_files",
    "prompt_file_contents",
    "prompt_files_in_sync",
    "prompt_registry",
    "prompt_versions_for",
    "prompts_root",
]
