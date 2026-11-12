"""Model-free SEC checks for structured proposals. Never publishes model prose.

The caller supplies a separately reviewed issuer registry. A model must not create
or modify that registry. Unknown identity, unit or period means omission.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from .edgar import EdgarClient


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def cik(value: Any) -> str | None:
    text = str(value)
    return text.zfill(10) if text.isascii() and text.isdigit() and 0 < len(text) <= 10 and int(text) > 0 else None


def finite(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def check_document(document: dict, issuers: dict, edgar: EdgarClient, *, enabled: bool = True) -> dict:
    if not isinstance(document, dict) or document.get("schema_version") != "sec-proposals-v1":
        raise ValueError("expected sec-proposals-v1")
    claims = document.get("claims")
    if not isinstance(claims, list) or len(claims) > 100:
        raise ValueError("claims must be a list of at most 100 items")
    if not isinstance(issuers, dict):
        raise ValueError("issuer registry must be an object")
    results = []
    ids = set()
    for proposal in claims:
        if not isinstance(proposal, dict) or not isinstance(proposal.get("id"), str) or not proposal["id"] or proposal["id"] in ids:
            raise ValueError("each claim requires a unique nonempty string id")
        ids.add(proposal["id"])
        row = {"id": proposal["id"], "status": "omitted", "reason": "verification_paused" if not enabled else "insufficient_evidence"}
        results.append(row)
        if not enabled:
            continue
        identity = issuers.get(proposal.get("issuer_key")) if isinstance(proposal.get("issuer_key"), str) else None
        if not isinstance(identity, dict) or identity.get("market") != "US" or not cik(identity.get("cik")):
            row["reason"] = "untrusted_issuer"
            continue
        ticker = identity.get("ticker")
        if not isinstance(ticker, str) or proposal.get("ticker") != ticker or cik(proposal.get("cik")) != cik(identity["cik"]):
            row["reason"] = "issuer_mismatch"
            continue
        resolved = edgar.resolve_ticker(ticker)
        if resolved.get("error") or cik(resolved.get("cik")) != cik(identity["cik"]):
            row["reason"] = "sec_identity_mismatch"
            continue
        if not all(isinstance(proposal.get(k), str) and proposal[k] for k in ("metric", "period", "unit")) or not finite(proposal.get("value")):
            row["reason"] = "invalid_claim"
            continue
        fact = edgar.lookup_fact(ticker, proposal["metric"], proposal["period"])
        if fact.get("error") or not finite(fact.get("value")) or not fact.get("source_sha256") or not fact.get("filing_url"):
            row["reason"] = fact.get("error", "missing_provenance")
            continue
        if cik(fact.get("cik")) != cik(identity["cik"]) or fact.get("unit") != proposal["unit"]:
            row["reason"] = "identity_or_unit_mismatch"
            continue
        # Always render a canonical bounded statement, not the model's original
        # sentence (which may contain additional unverified causal claims).
        if not fact.get("period") or fact["period"] == "LATEST":
            row["reason"] = "unresolved_period"
            continue
        value = fact["value"]
        status = "verified" if value == proposal["value"] else "corrected"
        row.update(status=status, reason="exact_sec_fact", evidence=fact,
                   statement=f"{ticker} {fact['period']} {fact['metric']}: {value:,} {fact['unit']}.")
    return {"schema_version": "sec-check-v1", "enabled": enabled,
            "input_sha256": digest(document), "issuer_registry_sha256": digest(issuers),
            "verification_policy": edgar.policy.to_dict(), "results": results,
            "publishable_statements": [r["statement"] for r in results if "statement" in r],
            "scope": "Structured SEC facts only; no validation of surrounding article or market forecasts."}
