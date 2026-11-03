"""Correct source-tier metadata without editing frozen gold or truth labels.

The pre-call builder incorrectly called all companyfacts values L1. Repository
policy distinguishes audited 10-K (L1), reviewed 10-Q (L2), derivations (L3)
and furnished releases (L4). This sidecar preserves the original run verbatim.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


def correct(node):
    if isinstance(node, list):
        return [correct(x) for x in node]
    if not isinstance(node, dict):
        return node
    node = {k: correct(v) for k, v in node.items()}
    if node.get("source_kind") == "companyfacts":
        node["tier"] = "L1" if node["fact"]["form"] in {"10-K", "10-K/A"} else "L2"
    if "formula" in node and "inputs" in node:
        node["tier"] = "L3"
    if node.get("kind") == "companyfacts":
        node.pop("tier", None)
        node["tier_policy"] = "Container includes multiple filing forms; classify each exact-period fact, not the API container."
    if "components" in node:
        node["tier"] = sorted({c["tier"] for c in node["components"]})
    return node


def build(out):
    raw = (out / "gold.jsonl").read_bytes()
    original = list(map(json.loads, raw.decode().splitlines()))
    corrected = correct(copy.deepcopy(original))
    if [(r["id"], r["gold_verdict"], r["gold_basis"]) for r in corrected] != [(r["id"], r["gold_verdict"], r["gold_basis"]) for r in original]:
        raise ValueError("metadata correction must not change truth labels")
    (out / "gold-source-tiers-corrected.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in corrected))
    lines = ["# Source-tier metadata correction", "",
             "The pre-call frozen builder incorrectly labelled every companyfacts value L1, including quarterly 10-Q facts, and labelled calculated growth L1. This is a metadata error against the repository's [source policy](../../../DATA_SOURCES.md#sec-evidence-tiers). The original gold, sources, builder and FREEZE remain byte-identical. Numeric values, periods, arithmetic, verdict labels, cases, scoring denominators and paid inputs are unchanged. No provider output was used to select or change a truth label.", "",
             "The [corrected metadata copy](gold-source-tiers-corrected.jsonl) is reproducible offline. Source `form` fields establish the distinction: audited annual 10-K values L1; reviewed quarterly 10-Q values L2; growth derived from two facts L3; furnished earnings releases L4. The companyfacts container itself has no single evidence tier.", "",
             f"Original frozen gold SHA-256: `{hashlib.sha256(raw).hexdigest()}`.", "",
             "| Case | Corrected component tiers | Meaning |", "|---|---|---|"]
    for r in corrected:
        if r["gold_basis"] == "primary_release":
            lines.append(f"| {r['id']} | {', '.join(r['tier'])} | " + "; ".join(f"{c['metric']}: {c['tier']}" for c in r['components']) + " |")
    lines += ["", "Registered while the agent pass was still running, before the post pass; this correction does not claim a second independent gold review. Accuracy continues to use the unchanged frozen verdict labels. See SCORING_NOTE.json for compound-item metrics.", ""]
    (out / "GOLD_METADATA_ERRATA.md").write_text("\n".join(lines))
    return corrected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    print("rows", len(build(parser.parse_args().out)))
