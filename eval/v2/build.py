#!/usr/bin/env python3
"""Validate and merge the v2 generated, paraphrased, and real-world layers."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = ROOT / ".cache"
DEFAULT_GENERATED = ROOT / "eval" / "v2" / "claims-generated.jsonl"
DEFAULT_PARAPHRASED = ROOT / "eval" / "v2" / "claims-paraphrased.jsonl"
DEFAULT_REAL = ROOT / "eval" / "v2" / "real.yaml"
DEFAULT_OUTPUT = ROOT / "eval" / "v2" / "claims-v2.jsonl"
DEFAULT_REVIEW = ROOT / "eval" / "v2" / "GOLD_REVIEW.md"
DEFAULT_MANIFEST = ROOT / "eval" / "v2" / "MANIFEST.json"
VALID_VERDICTS = {"supported", "contradicted", "insufficient_evidence"}
VALID_SPLITS = {"dev", "test"}


class BuildError(RuntimeError):
    """Raised for invalid v2 layer data or a gold disagreement."""


def _load_gold_reader() -> Any:
    path = ROOT / "eval" / "build_gold.py"
    name = "market_claim_v2_build_gold"
    loaded = sys.modules.get(name)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise BuildError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        # real.yaml is intentionally JSON-compatible, matching the v1 gold
        # builder.  If a later collector uses ordinary YAML and PyYAML is
        # available, accept it without making PyYAML a runtime dependency.
        if path.suffix.lower() in {".yaml", ".yml"}:
            try:
                import yaml  # type: ignore

                return yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        raise BuildError(f"unable to read {path}: {exc}") from exc


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise BuildError(f"invalid JSON on {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise BuildError(f"{path}:{line_number} is not an object")
            rows.append(value)
    return rows


def _real_claims(path: Path) -> list[dict[str, Any]]:
    value = _read_json(path)
    if isinstance(value, dict):
        value = value.get("claims")
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise BuildError(f"{path} must contain a claims list")
    return [dict(item) for item in value]


def validate_real_claims(claims: Iterable[Mapping[str, Any]]) -> None:
    """Validate the hand-collected layer before any gold calculation."""

    items = list(claims)
    ids = [item.get("id") for item in items]
    if any(not isinstance(item_id, str) or not re.fullmatch(r"R\d{2,}", item_id) for item_id in ids):
        raise BuildError("real ids must match R01, R02, ...")
    if len(set(ids)) != len(ids):
        raise BuildError("real ids must be unique")
    for item in items:
        item_id = str(item["id"])
        if not isinstance(item.get("source_url"), str) or not re.match(r"^https?://", item["source_url"]):
            raise BuildError(f"{item_id}: source_url must be an http(s) URL")
        for key in ("source_title", "published", "claim", "gold_note"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise BuildError(f"{item_id}: {key} is required")
        if len(item["claim"].split()) > 25:
            raise BuildError(f"{item_id}: claim must contain at most 25 words")
        if not isinstance(item.get("spec"), dict):
            raise BuildError(f"{item_id}: spec must be an object")
        if item.get("gold_verdict") not in VALID_VERDICTS:
            raise BuildError(f"{item_id}: invalid gold_verdict")
        if not isinstance(item.get("example", False), bool):
            raise BuildError(f"{item_id}: example must be boolean when present")


def _tickers_in_spec(spec: Mapping[str, Any]) -> set[str]:
    found: set[str] = set()
    ticker = spec.get("ticker")
    if ticker:
        found.add(str(ticker).upper())
    for key in ("parts",):
        value = spec.get(key)
        if isinstance(value, list):
            for part in value:
                if isinstance(part, Mapping):
                    found.update(_tickers_in_spec(part))
    return found


def _load_snapshots(bg: Any, cache_dir: Path, items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    tickers: set[str] = set()
    for item in items:
        spec = item.get("spec")
        if isinstance(spec, Mapping):
            tickers.update(_tickers_in_spec(spec))
    if not tickers:
        return {}
    ticker_map = bg._load_ticker_map(cache_dir)
    snapshots: dict[str, Any] = {}
    for ticker in sorted(tickers):
        try:
            snapshots[ticker] = bg.load_snapshot(cache_dir, ticker, ticker_map)
        except bg.GoldBuildError as exc:
            raise BuildError(str(exc)) from exc
    return snapshots


def _truth_verdict(truth: Any) -> str:
    if truth is True:
        return "supported"
    if truth is False:
        return "contradicted"
    return "insufficient_evidence"


def _family(item: Mapping[str, Any]) -> str:
    if item.get("family"):
        return str(item["family"])
    if item.get("category"):
        return str(item["category"])
    kind = str((item.get("spec") or {}).get("kind") if isinstance(item.get("spec"), Mapping) else "")
    return {
        "value": "value", "growth": "yoy", "first_time_above": "record_first",
        "period_trap": "period_trap", "multi": "multi_part", "not_checkable": "not_checkable",
        "ambiguous_period": "ambiguous_period",
    }.get(kind, kind or "unknown")


def _compact_source_facts(evaluated: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            if value.get("concept") is not None and value.get("value") is not None:
                row = {
                    "concept": value.get("concept"), "start": value.get("start"),
                    "end": value.get("end"), "accn": value.get("accn"),
                    "form": value.get("form"), "value": value.get("value"),
                    "file_sha256": value.get("source_sha256"),
                }
                key = tuple(row.values())
                if key not in seen:
                    seen.add(key)
                    rows.append(row)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(evaluated.get("facts", []))
    return rows


def _validate_period_basis(spec: Mapping[str, Any], item_id: str) -> None:
    kind = str(spec.get("kind") or "")
    if kind != "not_checkable":
        basis = spec.get("period_basis")
        if basis not in {"calendar", "fiscal", "month_named"}:
            raise BuildError(f"{item_id}: period_basis must be calendar, fiscal, or month_named")
    parts = spec.get("parts")
    if isinstance(parts, list):
        for part in parts:
            if isinstance(part, Mapping):
                _validate_period_basis(part, item_id)


def _validate_and_label(item: Mapping[str, Any], bg: Any, snapshots: Mapping[str, Any], *, layer: str) -> dict[str, Any]:
    item_id = str(item.get("id") or "")
    expected_pattern = {
        "generated": r"G\d{4}",
        "paraphrased": r"P\d{4}",
        "real": r"R\d{2,}",
    }[layer]
    if not re.fullmatch(expected_pattern, item_id):
        raise BuildError(f"{item_id or '<missing>'}: invalid {layer} id")
    if not isinstance(item.get("claim"), str) or not item["claim"].strip():
        raise BuildError(f"{item_id}: claim is required")
    spec = item.get("spec")
    if not isinstance(spec, Mapping):
        raise BuildError(f"{item.get('id')}: spec is required")
    _validate_period_basis(spec, item_id)
    try:
        evaluated = bg.evaluate_spec(spec, snapshots)
    except (KeyError, bg.GoldBuildError) as exc:
        raise BuildError(f"{item.get('id')}: spec evaluation failed: {exc}") from exc
    computed = _truth_verdict(evaluated.get("truth"))
    if item.get("gold_verdict") != computed:
        raise BuildError(f"{item.get('id')}: gold disagreement: claimed {item.get('gold_verdict')}, computed {computed}")
    output = dict(item)
    output["layer"] = layer
    output["family"] = _family(item)
    output.setdefault("category", output["family"])
    output.setdefault("split", "test")
    if output["split"] not in VALID_SPLITS:
        raise BuildError(f"{item.get('id')}: split must be dev or test")
    output["gold_note"] = str(evaluated.get("note") or item.get("gold_note") or "").replace("\n", " ")
    output["source_facts"] = output.get("source_facts") or _compact_source_facts(evaluated)
    if not isinstance(output["source_facts"], list):
        raise BuildError(f"{item_id}: source_facts must be a list")
    required_fact_fields = {"concept", "start", "end", "accn", "form", "value", "file_sha256"}
    for fact in output["source_facts"]:
        if not isinstance(fact, Mapping) or not required_fact_fields <= set(fact):
            raise BuildError(f"{item_id}: malformed source fact")
        digest = fact.get("file_sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise BuildError(f"{item_id}: source fact has invalid file_sha256")
    return output


def _input_manifest(path: Path, *, optional: bool) -> dict[str, Any]:
    return {"path": str(path), "exists": path.is_file(), "optional": optional, "sha256": _sha256(path)}


def _count_manifest(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    def counts(values: Iterable[Any]) -> dict[str, int]:
        return dict(sorted(Counter(str(value) for value in values).items()))

    companies: list[str] = []
    period_bases: list[str] = []
    for row in rows:
        spec = row.get("spec")
        if isinstance(spec, Mapping):
            companies.extend(sorted(_tickers_in_spec(spec)))
            basis = spec.get("period_basis")
            if basis is None:
                basis = next(
                    (part.get("period_basis") for part in _spec_parts(spec) if part.get("period_basis") is not None),
                    None,
                )
            if basis is not None:
                period_bases.append(str(basis))
    return {
        "total": len(rows),
        "by_layer": counts(row.get("layer") for row in rows),
        "by_family": counts(row.get("family") for row in rows),
        "by_verdict": counts(row.get("gold_verdict") for row in rows),
        "by_split": counts(row.get("split") for row in rows),
        "by_company": counts(companies),
        "by_period_basis": counts(period_bases),
    }


def _spec_parts(spec: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Flatten a spec enough to count period bases in multi claims."""

    result = [spec]
    parts = spec.get("parts")
    if isinstance(parts, list):
        for part in parts:
            if isinstance(part, Mapping):
                result.extend(_spec_parts(part))
    return result


def _review(rows: list[Mapping[str, Any]], path: Path, *, seed: int) -> list[str]:
    rng = random.Random(seed)
    sample_ids = {str(row.get("id")) for row in rng.sample(rows, min(40, len(rows)))} if rows else set()
    lines = [
        "# v2 gold review",
        "",
        "Rows marked `yes` in `spot_check_sample` are the deterministic sample for human review.",
        "Gold is computed from the independent SEC snapshot reader; this table is a review aid, not a second label source.",
        "",
        "| ID | Layer | Family | Split | Company | Period basis | Gold | Spot-check | Claim | Gold note |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        spec = row.get("spec") if isinstance(row.get("spec"), Mapping) else {}
        companies = ", ".join(sorted(_tickers_in_spec(spec))) or "—"
        period_bases = ", ".join(sorted({str(part.get("period_basis")) for part in _spec_parts(spec) if part.get("period_basis")})) or "—"
        claim = str(row.get("claim", "")).replace("|", "\\|").replace("\n", " ")
        note = str(row.get("gold_note", "")).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {row.get('id')} | {row.get('layer')} | {row.get('family')} | {row.get('split')} | {companies} | {period_bases} | {row.get('gold_verdict')} | {'yes' if str(row.get('id')) in sample_ids else 'no'} | {claim} | {note} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sorted(sample_ids)


def build_combined(
    *,
    generated_path: str | Path = DEFAULT_GENERATED,
    paraphrased_path: str | Path = DEFAULT_PARAPHRASED,
    real_path: str | Path = DEFAULT_REAL,
    cache_dir: str | Path = DEFAULT_CACHE,
    output_path: str | Path = DEFAULT_OUTPUT,
    review_path: str | Path = DEFAULT_REVIEW,
    manifest_path: str | Path = DEFAULT_MANIFEST,
    review_seed: int = 20261027,
) -> dict[str, Any]:
    bg = _load_gold_reader()
    generated = _jsonl(Path(generated_path))
    paraphrased = _jsonl(Path(paraphrased_path))
    real = _real_claims(Path(real_path)) if Path(real_path).is_file() else []
    validate_real_claims(real)
    accepted_paraphrases = [row for row in paraphrased if row.get("status", "accepted") == "accepted"]
    generated_by_id = {str(row.get("id")): row for row in generated}
    for row in accepted_paraphrases:
        paraphrase_id = str(row.get("id") or "<missing>")
        source_id = row.get("paraphrase_of")
        if not isinstance(source_id, str) or source_id not in generated_by_id:
            raise BuildError(f"{paraphrase_id}: paraphrase_of must reference a generated claim")
        source = generated_by_id[source_id]
        if row.get("spec") != source.get("spec"):
            raise BuildError(f"{paraphrase_id}: paraphrase spec differs from {source_id}")
        if row.get("gold_verdict") != source.get("gold_verdict"):
            raise BuildError(f"{paraphrase_id}: paraphrase gold differs from {source_id}")
        if row.get("split") != source.get("split"):
            raise BuildError(f"{paraphrase_id}: paraphrase split differs from {source_id}")
    # Examples are excluded from the run, but they still go through the same
    # gold self-check so a stale illustrative label cannot hide in the schema.
    all_inputs = generated + accepted_paraphrases + real
    snapshots = _load_snapshots(bg, Path(cache_dir), all_inputs)
    rows: list[dict[str, Any]] = []
    for row in generated:
        rows.append(_validate_and_label(row, bg, snapshots, layer="generated"))
    for row in accepted_paraphrases:
        rows.append(_validate_and_label(row, bg, snapshots, layer="paraphrased"))
    for row in real:
        validated = _validate_and_label(row, bg, snapshots, layer="real")
        if not row.get("example", False):
            rows.append(validated)
    ids = [str(row.get("id")) for row in rows]
    if len(ids) != len(set(ids)):
        raise BuildError("combined claim ids must be unique")
    rows.sort(key=lambda row: (str(row.get("layer")), str(row.get("id"))))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    sample_ids = _review(rows, Path(review_path), seed=review_seed)
    input_files = {
        "generated": _input_manifest(Path(generated_path), optional=False),
        "paraphrased": _input_manifest(Path(paraphrased_path), optional=True),
        "real": _input_manifest(Path(real_path), optional=False),
    }
    output_files = {
        "claims_v2": _input_manifest(output, optional=False),
        "gold_review": _input_manifest(Path(review_path), optional=False),
    }
    manifest = {
        "schema_version": 2,
        "inputs": input_files,
        "outputs": output_files,
        "manifest_self_hash_excluded": True,
        "counts": _count_manifest(rows),
        "excluded_examples": [str(row.get("id")) for row in real if row.get("example", False)],
        "gold_review_sample_ids": sample_ids,
        "generator_seed": review_seed,
    }
    manifest_file = Path(manifest_path)
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated", type=Path, default=DEFAULT_GENERATED)
    parser.add_argument("--paraphrased", type=Path, default=DEFAULT_PARAPHRASED)
    parser.add_argument("--real", type=Path, default=DEFAULT_REAL)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--seed", type=int, default=20261027)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = build_combined(
            generated_path=args.generated,
            paraphrased_path=args.paraphrased,
            real_path=args.real,
            cache_dir=args.cache_dir,
            output_path=args.output,
            review_path=args.review,
            manifest_path=args.manifest,
            review_seed=args.seed,
        )
    except (BuildError, OSError, ValueError) as exc:
        print(f"v2 build failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

