# Paired multimodal benchmark v1 — recorded results

[Frozen protocol and exact inputs](../../../eval/multimodal-v1/README.md) · [machine-readable results and case index](summary.json) · [ledger](ledger.jsonl) · [cost basis](cost-basis.json) · [official rate cross-check](RATE_CHECK.md) · [execution log](execution.log) · [selected development profiles](selected-profiles.json) · [reuse guide](REUSE.md) · [artifact audit](audit.json)

Six test issuers, four assertions each, nine encodings: **24 underlying assertions / six issuer clusters**. Scores below describe this controlled corpus, not real-world accuracy. Clean synthetic cards and speech are deliberately easier than real earnings calls. Three real Tesla slide pages are reported separately without accuracy labels. All missing/failed/unmatched assertions remain wrong; conflicting duplicates do not get best-of selection.

The pipeline uses one shared Meta OCR/ASR result per file, then the same frozen text for each verifier. Native image reading is a separate study below. Meta Muse Spark 1.3 and the two pinned Muse Spark Open endpoints are different model/serving configurations. This compares the integrated Muse models, not every model offered by each platform. The selected profile is the best of **two development settings only**, not a claim to the globally best configuration. The default/low profile changes verification reasoning; short-input extraction retains the repository default reasoning, while partitioned long-input extraction uses low. Native image calls explicitly use the selected profile.

## Strict end-to-end verdict accuracy

| Format | Meta | Baseten | Fireworks |
| --- | --- | --- | --- |
| TXT | 22/24 (91.7%) | 24/24 (100.0%) | 24/24 (100.0%) |
| MD | 22/24 (91.7%) | 24/24 (100.0%) | 24/24 (100.0%) |
| PDF | 23/24 (95.8%) | 24/24 (100.0%) | 24/24 (100.0%) |
| PNG | 24/24 (100.0%) | 24/24 (100.0%) | 24/24 (100.0%) |
| JPG | 22/24 (91.7%) | 24/24 (100.0%) | 24/24 (100.0%) |
| WEBP | 23/24 (95.8%) | 24/24 (100.0%) | 24/24 (100.0%) |
| WAV | 18/24 (75.0%) | 23/24 (95.8%) | 24/24 (100.0%) |
| MP3 | 14/24 (58.3%) | 24/24 (100.0%) | 24/24 (100.0%) |
| MP4 | 19/24 (79.2%) | 24/24 (100.0%) | 24/24 (100.0%) |

## Coverage, false support and abstention

| Provider / format | Gold extracted | Gold checked | False supported / negative gold | Insufficient-evidence predictions | Empirical issuer-bootstrap range (95%; exploratory) |
| --- | --- | --- | --- | --- | --- |
| meta / txt | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 8 | 75.0%–100.0% |
| meta / md | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 8 | 75.0%–100.0% |
| meta / pdf | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 7 | 87.5%–100.0% |
| meta / png | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| meta / jpg | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 8 | 83.3%–100.0% |
| meta / webp | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 7 | 87.5%–100.0% |
| meta / wav | 20/24 (83.3%) | 20/24 (83.3%) | 0/12 (0.0%) | 7 | 45.8%–95.8% |
| meta / mp3 | 16/24 (66.7%) | 16/24 (66.7%) | 0/12 (0.0%) | 6 | 25.0%–91.7% |
| meta / mp4 | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 7 | 66.7%–91.7% |
| baseten / txt | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| baseten / md | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| baseten / pdf | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| baseten / png | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| baseten / jpg | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| baseten / webp | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| baseten / wav | 24/24 (100.0%) | 23/24 (95.8%) | 0/12 (0.0%) | 5 | 87.5%–100.0% |
| baseten / mp3 | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| baseten / mp4 | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| fireworks / txt | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| fireworks / md | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| fireworks / pdf | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| fireworks / png | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| fireworks / jpg | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| fireworks / webp | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| fireworks / wav | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| fireworks / mp3 | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |
| fireworks / mp4 | 24/24 (100.0%) | 24/24 (100.0%) | 0/12 (0.0%) | 6 | All observed clusters equal; bootstrap uninformative |

Extraction means deterministic ticker/metric/period alignment, not exact number transcription. Unmatched extractions are retained in JSON; alignment errors can reduce the strict score. No observed false support on this small controlled set is not a zero-risk guarantee; only 12 underlying negative/insufficient assertions are repeated across formats. The six-cluster bootstrap is exploratory and fragile: it resamples these selected issuers, not a representative population. Identical observed cluster scores give a degenerate bootstrap, not certainty of true accuracy. There is no pooled 216-independent-claim confidence interval or broad vendor ranking. This is one recorded run without a repeated-inference variability study; the bootstrap does not measure model randomness.

## Error categories

[Every scored miss](error-analysis.json) links to the original result; [reviewed examples](OBSERVATIONS.md) distinguish transcription, output-limit and quotation failures. Categories describe outcomes, not a guessed root cause. Repeated encodings can share one failed text job.

| Provider | Missing with pipeline error | Not aligned | Unresolved | Channel disagreement | Abstained on answerable gold | Unsafe support | Other wrong definitive verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| meta | 12 | 0 | 0 | 4 | 13 | 0 | 0 |
| baseten | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| fireworks | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Native image reading

| Provider / format | Completed / planned | Number-token recall | Word edit rate |
| --- | --- | --- | --- |
| meta / png | 6/6 | 72/72 (100.0%) | 0.0% |
| meta / jpg | 6/6 | 72/72 (100.0%) | 0.0% |
| meta / webp | 6/6 | 72/72 (100.0%) | 0.0% |
| baseten / png | 6/6 | 72/72 (100.0%) | 0.0% |
| baseten / jpg | 6/6 | 72/72 (100.0%) | 0.3% |
| baseten / webp | 6/6 | 72/72 (100.0%) | 0.0% |
| fireworks / png | 6/6 | 72/72 (100.0%) | 0.0% |
| fireworks / jpg | 6/6 | 72/72 (100.0%) | 0.0% |
| fireworks / webp | 6/6 | 72/72 (100.0%) | 0.0% |

These descriptive post-run reading metrics are not financial-verdict accuracy or image-authenticity checks. The native-image probe does not change product routing: `ingest` still uses Meta OCR for all three text providers. Number recall uses unsigned numeral tokens, includes dates/quarters, and does not validate signs, unit binding or table relationships; word edits can penalize harmless formatting or wording. Failed/missing text scores as missing words. Native reading uses the profile selected on development verification, not a separately optimized OCR profile. Native audio/video endpoints were **not tested**, so no unsupported-format conclusion follows.

## Actual spend and observed latency

| Platform | Estimated or reserved USD, all phases | Authorized cap | Chosen profile | Unique test text jobs | Median / maximum test text-job seconds |
| --- | --- | --- | --- | --- | --- |
| meta | $4.23601935 | $40 | low | 42 | 123.222 / 161.956 |
| baseten | $1.95196625 | $40 | low | 42 | 25.635 / 33.839 |
| fireworks | $2.01364550 | $40 | low | 42 | 165.021 / 238.813 |

All shared preprocessing is billed to Meta in this ledger. Spend includes development, diagnostics and failures; unreconciled reservations remain charged conservatively. Latency includes only unique text jobs referenced by the test split. These are usage estimates, **not invoices**. Per-format workflow unit estimates are in JSON and must not be summed as actual spending: identical text results can be reused. Fresh text jobs can contain extraction plus multiple agent tool calls. They exclude OCR/ASR and cache hits; observed concurrency/network effects mean this is not an SLA.

## Real issuer diagnostic pages

| Platform / Tesla page | Pipeline status | Extracted occurrences | Recorded verdicts |
| --- | --- | --- | --- |
| [meta / REAL-TSLA-4](diagnostic/meta/low/REAL-TSLA-4/ingest.json) | partial | 0 | {} |
| [meta / REAL-TSLA-5](diagnostic/meta/low/REAL-TSLA-5/ingest.json) | partial | 0 | {} |
| [meta / REAL-TSLA-23](diagnostic/meta/low/REAL-TSLA-23/ingest.json) | completed | 0 | {} |
| [baseten / REAL-TSLA-4](diagnostic/baseten/low/REAL-TSLA-4/ingest.json) | partial | 0 | {} |
| [baseten / REAL-TSLA-5](diagnostic/baseten/low/REAL-TSLA-5/ingest.json) | partial | 0 | {} |
| [baseten / REAL-TSLA-23](diagnostic/baseten/low/REAL-TSLA-23/ingest.json) | completed | 0 | {} |
| [fireworks / REAL-TSLA-4](diagnostic/fireworks/low/REAL-TSLA-4/ingest.json) | partial | 0 | {} |
| [fireworks / REAL-TSLA-5](diagnostic/fireworks/low/REAL-TSLA-5/ingest.json) | partial | 0 | {} |
| [fireworks / REAL-TSLA-23](diagnostic/fireworks/low/REAL-TSLA-23/ingest.json) | completed | 0 | {} |

No complete independent gold exists for these pages. Verdict counts are model/program outputs, not a claim that all page contents were found or correctly judged. See the machine index for native diagnostic responses as well.

## Reproduce without credits

Run `.venv/bin/python scripts/report_multimodal_benchmark.py` from the repository root. It recomputes scores from retained claim records and refuses mismatches. This does not rerun OCR, speech recognition or model calls. The original 72 files, three real diagnostic images, frozen prepared texts, requests, raw responses, failures and costs remain available. Media request payloads reference exact input/derived-media hashes instead of repeating base64.

The report uses the frozen scorer even when a wording mismatch is visible. Any future scorer correction, real-recording gold review or model change needs a separately labeled evaluation; this run remains immutable.
