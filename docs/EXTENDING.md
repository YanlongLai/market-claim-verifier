# Building your own verifier

The current product checks US-equity financial claims against SEC evidence. Changing a system prompt alone does not make it a reliable verifier in another domain. The [common evidence export interface and SEC connector](EVIDENCE_RECORDS.md) are implemented. A general plugin SDK and new non-SEC source integration remain planned.

## Start with an explicit question

Choose a narrow claim family, such as whether a US issuer reported a revenue value for a particular fiscal quarter. Specify the entity identifier, metric, units, period, supported comparisons and authoritative source. Distinguish “the issuer said this” from “this is true” and from “this forecast will happen.”

## Evidence contract

Every connector should emit a versioned record containing:

- Stable source identity and publisher; source URL or local artifact identity.
- Retrieval time, publication time, effective period and content SHA-256.
- Original bytes or a reproducible immutable snapshot, with quote offsets, page, table cell or audio time locator.
- Entity, metric, numeric value, unit, period and whether the value was reported or derived.
- Extraction method/version and quality limitations.
- Permitted claim types, authority scope and relations to amendments, duplicates and conflicting sources.

Source content is untrusted data, including instructions embedded in documents. It cannot change model policy, request credentials or authorize tools. Uploaded files are not automatically authoritative; a user document can be a claim source without becoming a ground-truth source. Two copies of one press release are not independent corroboration.

## Implementation sequence

1. Add source fixtures with attribution and exact hashes before writing a live connector.
2. Implement fetching/parsing separately from authority policy; retain failures and original text.
3. Add deterministic rules for entities, periods, units and admissible calculations; fail closed on missing context.
4. Adapt evidence to the existing tool loop without making model agreement a substitute for evidence.
5. Freeze a separate test set before tuning, including contradictory, insufficient, revised and malicious inputs.
6. Publish per-class quality, extraction recall, abstention, latency and cost. Keep post-hoc results labeled.
7. Document model/prompt/policy/source versions in every result and add offline replay fixtures.

## Reuse today

[Provider adapters](../src/claimcheck/providers.py), [budget accounting](../src/claimcheck/budget.py), [local ingestion](../src/claimcheck/ingest.py), source locations and trace recording can be reused. [Financial checks](../src/claimcheck/checks.py), SEC lookup tools, fiscal calendars and release-specific rules are domain-specific and require deliberate replacement for another domain.

Run `sh scripts/verify.sh` before publishing a change. It checks offline suites, fixture integrity, generated data and documentation links; it does not establish live provider compatibility or generalization. Add targeted live evaluations only with a bounded budget and separately recorded results.

## Maintenance

Keep data, engine and evaluation versions distinct. A source amendment should create a new version rather than overwrite history. Price updates need an effective date and source link; unknown prices must not silently become zero. Record reserved, estimated and reconciled costs separately. Re-evaluate when changing models, prompts, parsers, source authority or numeric rules.

Current prioritized work and delivery gates: [Day 5 plan](DAY5_PLAN.md). Current formats and costs: [provider comparison](PROVIDERS.md).
