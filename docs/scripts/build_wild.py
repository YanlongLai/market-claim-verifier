#!/usr/bin/env python3
"""Compile the saved real-world probes for /wild/, without network or model calls.

Both phases are required. A missing/incomplete record is an error, never a zero
or a sample result. All paths and hashes in the output refer to repository files.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path("docs/evidence/real-world-2026-11-02")
FIXCHECK = Path("docs/evidence/real-world-2026-11-03-fixcheck")
OUTPUT = Path("docs/wild/data.json")
PROVIDERS = ("baseten", "fireworks", "meta")
ROUTES = ("agent", "post")
VERDICTS = {"supported", "contradicted", "insufficient_evidence"}
STATUSES = {"completed", "failed", "partial_failure", "budget_stopped"}


class EvidenceError(ValueError):
    """The stored evidence is absent, incomplete or internally inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def number(value, label: str) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0, f"Invalid {label}: {value!r}")
    return value


def decimal_text(value, label: str) -> str:
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise EvidenceError(f"Invalid {label}: {value!r}") from error
    require(result.is_finite(), f"Non-finite {label}")
    return format(result, "f")


def source_url(value: str, *, sec: bool = False) -> str:
    parsed = urlsplit(value)
    require(parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username,
            f"Unsafe source URL: {value!r}")
    if sec:
        require(parsed.hostname in {"www.sec.gov", "data.sec.gov", "sec.gov"},
                f"Filing source must be SEC: {value!r}")
    return value


class Reader:
    def __init__(self, root: Path):
        self.root = root
        self.hashes: dict[str, str] = {}

    def text(self, path: Path) -> str:
        file = self.root / path
        require(file.is_file(), f"Required evidence missing: {path}. Merge the completed evidence before building /wild/.")
        raw = file.read_bytes()
        self.hashes[path.as_posix()] = hashlib.sha256(raw).hexdigest()
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise EvidenceError(f"Invalid evidence text: {path}: {error}") from error

    def read(self, path: Path):
        text = self.text(path)
        try:
            return [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" else json.loads(text)
        except json.JSONDecodeError as error:
            raise EvidenceError(f"Invalid evidence JSON: {path}: {error}") from error

    def rows(self, path: Path) -> dict:
        rows = self.read(path)
        require(isinstance(rows, list) and bool(rows), f"Empty or invalid evidence: {path}")
        require(all(isinstance(r, dict) and isinstance(r.get("id"), str) for r in rows),
                f"Every evidence row needs an id: {path}")
        require(len({r["id"] for r in rows}) == len(rows),
                f"Duplicate ids/attempts in {path}; never select a preferred attempt")
        return {r["id"]: r for r in rows}


def outcome(row: dict) -> str:
    require(row.get("status") in STATUSES, f"Unknown result status for {row['id']}: {row.get('status')}")
    if row["status"] != "completed":
        return row["status"]
    require(row.get("verdict") is None or row["verdict"] in VERDICTS,
            f"Unknown verdict for {row['id']}: {row.get('verdict')}")
    return row.get("verdict") or "skipped"


def summarize(cases: dict, gold: dict, results: dict) -> dict:
    rows = [results[key] for key in cases]
    outcomes = Counter(outcome(row) for row in rows)
    costs = [number(r["cost_usd"], f"cost for {r['id']}") for r in rows]
    latencies = [number(r["wall_seconds"], f"latency for {r['id']}") for r in rows
                 if r["status"] != "budget_stopped"]
    primary = [r for r in rows if gold[r["id"]]["gold_basis"] == "primary_release"]
    scope = [key for key in cases if gold[key]["gold_basis"] == "scope_policy"]
    scope_types = Counter()
    for key in scope:
        case = cases[key]
        kind = ("taiwan" if case.get("market") == "tw" else
                "price_moves" if case["claim_type"] == "price_move" else
                "private_companies" if case["claim_type"] == "private_company" else "other")
        scope_types[kind] += 1
    n = len(rows)
    total = math.fsum(costs)
    return {
        "items": n,
        "attempted": sum(r["status"] != "budget_stopped" for r in rows),
        "outcomes": {name: outcomes[name] for name in sorted(VERDICTS | {"skipped", "failed", "partial_failure", "budget_stopped"})},
        "primary_truth": {
            "correct": sum(r["status"] == "completed" and r.get("verdict") == gold[r["id"]]["gold_verdict"] for r in primary),
            "items": len(primary),
        },
        "review_unscored": sum(gold[key]["gold_basis"] == "review_required" for key in cases),
        "outside_check": {"items": len(scope), "share": len(scope) / n,
                          "by_reason": {key: scope_types[key] for key in ("taiwan", "price_moves", "private_companies", "other")}},
        "cost_usd": total,
        "cost_per_item_usd": total / n,
        "latency_seconds": {"n": len(latencies), "mean": statistics.mean(latencies) if latencies else None,
                            "p50": statistics.median(latencies) if latencies else None,
                            "p95": sorted(latencies)[math.ceil(len(latencies) * .95) - 1] if latencies else None},
    }


def read_phase(reader: Reader, path: Path, *, threads: bool) -> dict:
    cases = reader.rows(path / "claims.jsonl")
    gold = reader.rows(path / "gold.jsonl")
    require(cases.keys() == gold.keys(), f"Claim/gold inventory mismatch: {path}")
    for key, case in cases.items():
        require(gold[key].get("gold_basis") in {"primary_release", "scope_policy", "review_required"},
                f"Unknown gold basis: {path}/{key}")
        require(gold[key].get("claim_sha256") == hashlib.sha256(case["claim"].encode()).hexdigest(),
                f"Claim/gold hash mismatch: {path}/{key}")
        if gold[key]["gold_basis"] == "primary_release":
            require(gold[key].get("gold_verdict") in VERDICTS, f"Missing primary verdict: {key}")
    # Final metrics are published only after the evidence job has closed the run.
    metrics = reader.read(path / "metrics.json")
    reader.read(path / "RUN_END.json")
    groups = ("own_posts", "third_party_threads") if threads else ("news",)
    sources = {name: {key: c for key, c in cases.items() if not threads or c["source_group"] == name} for name in groups}
    require(sum(map(len, sources.values())) == len(cases) and all(sources.values()), f"Unknown/empty source groups: {path}")
    systems = {}
    for provider in PROVIDERS:
        for route in ROUTES:
            name = f"{provider}/{route}"
            rows = reader.rows(path / provider / route / "results.jsonl")
            require(rows.keys() == cases.keys(), f"Incomplete result inventory: {path}/{name}; retain budget stops and failures")
            total = summarize(cases, gold, rows)
            recorded = metrics["systems"][name]
            require(recorded["items"] == total["items"], f"Metrics item count mismatch: {path}/{name}")
            counts = {k: v for k, v in recorded["outcomes"].items() if v}
            require(counts == {k: v for k, v in total["outcomes"].items() if v}, f"Metrics outcome mismatch: {path}/{name}")
            require(math.isclose(recorded["cost_usd"], total["cost_usd"], abs_tol=1e-8), f"Metrics cost mismatch: {path}/{name}")
            systems[name] = {group: summarize(subset, gold, rows) for group, subset in sources.items()}
    return {"cases": cases, "gold": gold, "systems": systems, "metrics": metrics,
            "sources": {group: len(subset) for group, subset in sources.items()}}


def caught_cards(reader: Reader, phase: dict) -> list[dict]:
    path = EVIDENCE / "threads"
    corrected = reader.rows(path / "gold-source-tiers-corrected.jsonl")
    require(corrected.keys() == phase["gold"].keys(), "Corrected gold inventory mismatch")
    cards = []
    for key, case in phase["cases"].items():
        gold = corrected[key]
        require(gold["gold_verdict"] == phase["gold"][key]["gold_verdict"], f"Tier correction changed truth label: {key}")
        original = phase["gold"][key]
        require(gold.get("claim_sha256") == original.get("claim_sha256"), f"Tier correction changed claim hash: {key}")
        fields = ("metric", "claimed_value", "reference_value", "verdict")
        values = lambda row: [[c.get(field) for field in fields] for c in row.get("components", [])]
        require(values(gold) == values(original), f"Tier correction changed reference values: {key}")
        if case["source_group"] != "third_party_threads" or gold["gold_basis"] != "primary_release" or gold["gold_verdict"] != "contradicted":
            continue
        post = source_url(case["url"])
        parsed = urlsplit(post)
        require(parsed.hostname in {"www.threads.com", "www.threads.net", "threads.com", "threads.net"}
                and parsed.path.startswith("/@"), f"Missing Threads attribution: {key}")
        components = []
        for component in gold["components"]:
            if component["verdict"] != "contradicted":
                continue
            source = component.get("source", {})
            components.append({
                "metric": component["metric"],
                "claimed": decimal_text(component["claimed_value"], f"claimed value: {key}"),
                "filed": decimal_text(component["reference_value"], f"filed value: {key}"),
                "unit": "percent" if "growth" in component["metric"].lower() else "USD",
                "source_url": source_url(source["url"], sec=True),
                "tier": component["tier"],
            })
        require(bool(components), f"Contradicted card lacks sourced conflicting components: {key}")
        # Display language is recorded; translation causation is not inferred.
        likely_translation = gold.get("likely_unit_translation_error") is True
        require(not likely_translation or bool(gold.get("translation_error_evidence")),
                f"Translation label lacks evidence: {key}")
        cards.append({"id": key, "handle": parsed.path.split("/")[1], "post_url": post,
                      "posted": case["posted"], "shown": case["shown"],
                      "auto_translated": "auto-translated" in case["shown"],
                      "verdict": gold["gold_verdict"], "components": components,
                      "likely_unit_translation_error": likely_translation,
                      "evidence_path": (path / "gold-source-tiers-corrected.jsonl").as_posix()})
    # Lead with the Apple iPhone receipt; retain every independently refuted post.
    return sorted(cards, key=lambda c: (not any("iPhone" in x["metric"] for x in c["components"]), c["id"]))


def fixcheck_report(reader: Reader) -> dict:
    """Retain explicit before/after table cells when no structured summary exists.

    Evidence jobs need not adopt a presentation-only JSON schema. Report wording
    stays visible as source text; a prose-only or unfinished report fails closed.
    """
    path = FIXCHECK / "REPORT.md"
    report = reader.text(path)
    require(bool(re.search(r"post[ -]?hoc|事後", report, re.I)), f"Fixcheck report must identify its post-hoc scope: {path}")
    comparisons = []
    header = None
    for line in report.splitlines():
        if not line.lstrip().startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        names = [c.strip(" *`").lower() for c in cells]
        before = next((i for i, value in enumerate(names) if re.match(r"before\b|修正前", value)), None)
        after = next((i for i, value in enumerate(names) if re.match(r"after\b|修正後", value)), None)
        if before is not None and after is not None:
            # Do not copy a third-party claim/body column into the public page.
            label = next((i for i, value in enumerate(names) if re.match(r"case\b|id\b|fix\b|change\b|check\b|area\b|案例|修正項目", value)), None)
            header = (len(cells), before, after, label)
            continue
        if header is None or all(re.fullmatch(r"[: -]+", c) for c in cells):
            continue
        require(len(cells) == header[0], f"Malformed before/after table: {path}")
        _, before, after, label = header
        require(bool(cells[before]) and bool(cells[after]), f"Incomplete before/after row: {path}")
        title = cells[label] if label is not None else None
        comparisons.append({"id": f"report-row-{len(comparisons) + 1}",
                            "description": {"en": title or "Known-case recheck", "zh": title or "已知案例重測"},
                            "before": cells[before], "after": cells[after], "evidence_path": path.as_posix()})
    require(bool(comparisons), f"No explicit Before/After table in {path}; retain comparisons in the report or summary.json")
    return {"kind": "posthoc_fixcheck", "report_excerpt": True, "comparisons": comparisons}


def read_fixcheck(reader: Reader) -> dict | None:
    if not (reader.root / FIXCHECK).exists():
        return None
    # A present directory is never silently treated as an absent recheck.
    summary = reader.read(FIXCHECK / "summary.json") if (reader.root / FIXCHECK / "summary.json").exists() else fixcheck_report(reader)
    require(summary.get("kind") == "posthoc_fixcheck" and isinstance(summary.get("comparisons"), list) and bool(summary["comparisons"]),
            f"Unsupported fixcheck schema: {FIXCHECK}/summary.json")
    for row in summary["comparisons"]:
        require(all(key in row for key in ("id", "description", "before", "after", "evidence_path")),
                "Fixcheck comparison needs description, before/after and evidence_path")
        for field in ("description", "before", "after"):
            value = row[field]
            require((isinstance(value, str) and bool(value.strip())) or
                    (isinstance(value, dict) and all(isinstance(value.get(lang), str) and value[lang].strip() for lang in ("en", "zh"))),
                    f"Fixcheck {field} must be source text or complete EN/中文 text")
        evidence = Path(row["evidence_path"])
        require(not evidence.is_absolute() and ".." not in evidence.parts and evidence.parts[:1] == ("docs",),
                "Fixcheck evidence path must be repository-relative under docs/")
        reader.text(evidence) if evidence.suffix == ".md" else reader.read(evidence)
    return summary


def build(root: Path = ROOT) -> dict:
    reader = Reader(root)
    news = read_phase(reader, EVIDENCE, threads=False)
    threads = read_phase(reader, EVIDENCE / "threads", threads=True)
    selection = reader.read(EVIDENCE / "threads/selection.json")
    require(selection["own_selected"] == threads["sources"]["own_posts"], "Threads selection count mismatch")
    cards = caught_cards(reader, threads)
    fixcheck = read_fixcheck(reader)
    return {
        "schema_version": 1,
        "study_kind": "development_probe",
        "sources": [{"id": group, "phase": phase, "items": count,
                     "report_path": (EVIDENCE / "REPORT.md").as_posix()}
                    for phase, part in ((1, news), (2, threads)) for group, count in part["sources"].items()],
        "systems": {name: {**news["systems"][name], **threads["systems"][name]} for name in news["systems"]},
        "phase_costs_usd": {"news": number(news["metrics"]["total_cost_usd"], "News ledger total"),
                            "threads_including_media": number(threads["metrics"]["total_cost_usd"], "Threads ledger total")},
        "engagement_metrics": selection["engagement_metrics"],
        "cards": cards,
        "fixcheck": fixcheck,
        "evidence_sha256": dict(sorted(reader.hashes.items())),
    }


def serialize(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root (also used by fixture tests)")
    parser.add_argument("--output", type=Path, help="Default: ROOT/docs/wild/data.json")
    parser.add_argument("--check", action="store_true", help="Fail unless the saved output is byte-identical")
    args = parser.parse_args()
    output = args.output or args.root / OUTPUT
    try:
        payload = serialize(build(args.root))
        if args.check:
            require(output.is_file() and output.read_bytes() == payload, f"Stale or missing output: {output}")
            print("PASS wild data: byte-identical saved evidence rebuild")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(payload)
            print(f"Built {output} from saved evidence (no network)")
    except (EvidenceError, OSError, KeyError, TypeError) as error:
        print(f"FAIL wild evidence: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
