# One official source, three different outcomes

**Offline deterministic walkthrough.** Three predefined atomic claims use one recorded Meta Platforms SEC earnings-release quote. No live model, OCR, ASR, network retrieval or extraction is run. This is an illustrative regression example, not an accuracy benchmark or a saved model conversation.

## Inspect the result

| Claim | Program verdict | Why |
|---|---|---|
| META expects revenue of $47.5 billion to $50.5 billion for FY2025Q3. | **supported** | Both stated endpoints match the issuer outlook for the same quarter. |
| META expects revenue of $48.5 billion to $51.5 billion for FY2025Q3. | **contradicted** | Both endpoints are $1 billion above the selected issuer outlook. |
| META expects revenue of $47.5 billion to $50.5 billion for FY2025Q4. | **insufficient_evidence** | The selected quote concerns Q3, not Q4. Matching numbers cannot repair a period mismatch. This example does not establish that no Q4 disclosure exists elsewhere. |

[Open the exact official-source excerpt](SOURCE.md#verified-excerpt) · [Complete source provenance](SOURCE.md) · [Machine-readable checks and costs](results.json)

All three cases select the same quote. The third check rejects its applicability: evidence selection is not evidence acceptance. No model-proposed verdict is needed; the existing financial checker produces the outcome. Read each `program_check.reason`, `actual_range` and `stated_range` in the JSON for the program output.

## What this costs

| Stage | Incremental API cost USD | Reason |
|---|---:|---|
| Source retrieval | 0 | Committed local snapshot; network fallback disabled |
| OCR / ASR | 0 | Existing HTML text |
| Claim extraction | 0 | Three predefined inputs |
| Verification model | 0 | Deterministic Python rules |
| Total | **0** | **0 API requests** |

Local CPU/storage is not metered; historical acquisition cost is not reconstructed. This is not a quote for live agent verification. See the [provider comparison](https://github.com/YanlongLai/market-claim-verifier/blob/main/docs/PROVIDERS.md) for dated model rates and recorded live costs.

## Reproduce

From the repository root:

```sh
uv run python examples/evidence/judge_walkthrough.py --out /tmp/claimcheck-judge
```

Open the generated `REPORT.md`. The output retains original bytes, normalized text, a versioned evidence record and full deterministic checks. Source and quote integrity are rechecked; a changed existing evidence artifact is rejected instead of overwritten.

## Limits

US issuer guidance only, from one chosen recorded document. No arbitrary uploaded document becomes authoritative. No current/live source freshness, exhaustive retrieval, extraction recall or general accuracy is claimed. All outcomes concern the issuer's statement, not the truth of future financial performance.

Record ID: `2713b2e5f01f3dbee9c3570e4d477e1c30bdd424a25d0a06d2d527f482346008`.
