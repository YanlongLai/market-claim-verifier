# Threads findings and retained failures

This is a selected real-input coverage probe. Five primary-source truth items cannot establish broad accuracy; review and scope labels have different meanings. No post-run product repair or outcome-driven paid repeat was made.

## Independent truth cases

| Case | Frozen gold | baseten/agent | baseten/post | fireworks/agent | fireworks/post | meta/agent | meta/post |
|---|---|---|---|---|---|---|---|
| T02 | supported | [supported](baseten/agent/T02/result.json) | [supported](baseten/post/T02/result.json) | [supported](fireworks/agent/T02/result.json) | [supported](fireworks/post/T02/result.json) | [supported](meta/agent/T02/result.json) | [supported](meta/post/T02/result.json) |
| T03 | contradicted | [contradicted](baseten/agent/T03/result.json) | [contradicted](baseten/post/T03/result.json) | [contradicted](fireworks/agent/T03/result.json) | [failed](fireworks/post/T03/result.json) | [contradicted](meta/agent/T03/result.json) | [contradicted](meta/post/T03/result.json) |
| T09 | contradicted | [insufficient_evidence](baseten/agent/T09/result.json) | [contradicted](baseten/post/T09/result.json) | [failed](fireworks/agent/T09/result.json) | [contradicted](fireworks/post/T09/result.json) | [insufficient_evidence](meta/agent/T09/result.json) | [insufficient_evidence](meta/post/T09/result.json) |
| T19 | supported | [insufficient_evidence](baseten/agent/T19/result.json) | [insufficient_evidence](baseten/post/T19/result.json) | [failed](fireworks/agent/T19/result.json) | [failed](fireworks/post/T19/result.json) | [insufficient_evidence](meta/agent/T19/result.json) | [insufficient_evidence](meta/post/T19/result.json) |
| T33 | contradicted | [insufficient_evidence](baseten/agent/T33/result.json) | [failed](baseten/post/T33/result.json) | [failed](fireworks/agent/T33/result.json) | [contradicted](fireworks/post/T33/result.json) | [insufficient_evidence](meta/agent/T33/result.json) | [contradicted](meta/post/T33/result.json) |

T02 is Alphabet's explicit Q3 2026 revenue and growth; T19 is AMD's explicit FY2026 Q2 revenue, growth, adjusted EPS, segment revenue and guidance. T03, T09 and T33 contain independently refuted unit or comparison-period components. Exact source coordinates/arithmetic are in [frozen gold](gold.jsonl). An insufficient response on a supported primary case counts wrong, even when abstention is safe operationally.

## Longest observed text item per path

Wall time includes extraction/checking, retrieval and retries. These maxima complement the full mean/median/p95 distributions; they are not isolated API speed measurements.

| Provider/path | Item | Seconds | Status |
|---|---|---:|---|
| baseten/agent | [T32](baseten/agent/T32/result.json) | 57.11 | completed |
| baseten/post | [T19](baseten/post/T19/result.json) | 80.18 | completed |
| fireworks/agent | [O06](fireworks/agent/O06/result.json) | 435.95 | completed |
| fireworks/post | [T33](fireworks/post/T33/result.json) | 864.85 | completed |
| meta/agent | [T09](meta/agent/T09/result.json) | 230.53 | completed |
| meta/post | [T33](meta/post/T33/result.json) | 269.81 | completed |

## Issuer binding and scope

[Baseten N03 trace](baseten/agent/N03/trace.json) maps **SM Entertainment**, a Korean issuer named in a KRW claim, to **SM ENERGY CO**, ticker `SM`, CIK `0000893538`, using USD facts and an unstated 2025 period. The resulting contradiction is an invalid issuer comparison. This repeats the kind of binding failure found in phase 1's Hon Precision → Honeywell case. A low false-supported rate does not exclude harmful false contradictions. The current production check validates selected evidence arithmetic without independently establishing that this is the company named by the input.

Every decisive output on scope-only gold is listed below. These are operational disagreements, not independent truth adjudications of those posts.

| Provider/path | Scope item | Aggregate verdict | Any supported extraction |
|---|---|---|---|
| baseten/agent | [N03](baseten/agent/N03/result.json) | contradicted | False |
| baseten/agent | [O06](baseten/agent/O06/result.json) | contradicted | False |
| fireworks/agent | [N03](fireworks/agent/N03/result.json) | contradicted | False |
| fireworks/agent | [O06](fireworks/agent/O06/result.json) | contradicted | False |

## Media completion and privacy

Each card ran through the actual image-ingest CLI once per verifier provider, with fresh Meta vision on every route. The authoring agent's visual review was frozen before paid OCR; no independent human reference transcript or truth adjudication was supplied. The frozen flag named `human_visual_review_before_ocr` is inaccurate provenance wording, corrected in [the media review notice](MEDIA_REVIEW_PROVENANCE.md) without changing original gold. Original cards and verbatim responses remain local and ignored. Public records retain request/reservation metadata and hashes of every full artifact.

| Route | Status | OCR completed requests | Incomplete text requests | Proposals | Checked claims | Seconds | USD route |
|---|---|---:|---:|---:|---:|---:|---:|
| [baseten/M01](media/baseten/M01/result.json) | partial_failure | 1 | 1 | 0 | 0 | 22.00 | 0.023711 |
| [baseten/M02](media/baseten/M02/result.json) | partial_failure | 1 | 1 | 0 | 0 | 20.24 | 0.020714 |
| [fireworks/M01](media/fireworks/M01/result.json) | partial_failure | 1 | 0 | 0 | 0 | 111.30 | 0.026180 |
| [fireworks/M02](media/fireworks/M02/result.json) | partial_failure | 0 | 0 | 0 | 0 | 36.83 | 0.015264 |
| [meta/M01](media/meta/M01/result.json) | partial_failure | 1 | 1 | 0 | 0 | 37.91 | 0.023048 |
| [meta/M02](media/meta/M02/result.json) | partial_failure | 1 | 1 | 0 | 0 | 35.73 | 0.018977 |

Five OCR requests completed. Fireworks/M02 stopped on incomplete Meta OCR before text extraction; Fireworks/M01 completed OCR but its text extraction raised `APITimeoutError`. The other four routes returned incomplete text extraction. All six routes produced zero proposals and zero checked claims. The earlier in-progress summary that all six completed OCR and had incomplete text extraction was inaccurate; the retained request records above distinguish the stages.

Media claim extraction uses the registered 3,000-token output limit (text-post extraction uses the phase-1 4,000-token default). Incomplete responses stay failures; no budget increase or repeated paid extraction was selected after observing them. OCR completion alone does not establish OCR fidelity. Text-only analysis of the frozen outputs would not retest image reading.

## Translation and compound claims

The report separately identifies T33's approximately tenfold Apple segment discrepancies, T03's CoreWeave unit/YTD problems, T09's sequential-versus-year-over-year growth and T10's unscored apparent unit-error candidate. Original-language causation was not verified. Preserve the shown input; do not silently replace it with a corrected number.

Post-level supported means the checked extracted rows were all supported; unchecked source assertions can remain. Coverage is therefore reported separately from aggregate accuracy. True extracted components within a refuted compound post are counted in `any_supported_component_on_negative_post_NOT_false_support`, while an entirely supported aggregate on refuted gold is false support. Scope-only items retain phase-1's any-supported rule. Missing reporting years/metric definitions remain on the [review list](GOLD_REVIEW.md).

## Follow-up work

Bind issuer identity/currency before arithmetic; expose incomplete extraction as failed coverage; align every material component in compound posts; obtain explicit period context rather than guessing from publication dates; retain shown-language unit provenance. Start with offline replay of these retained failures. Future real audio/video uses [Owner-provided DappGo Reels/YouTube files](../NEXT_SOURCES.md), with independent references, frozen gold and a new explicit budget.
