# Reviewed findings and improvement hypotheses

These are post-run inspections of retained examples, not changes to the frozen scorer, prompts or selected settings. They do not revise the benchmark's strict scores. Future fixes require a separately labeled regression and a new held-out study.

## An audio miss can occur after correct transcription

In [Meta / AMZN / MP3](test/meta/low/AMZN-mp3/ingest.json), the prepared transcript retains the EPS value **1.89**, the company and fiscal Q3 2026. The extracted sentence retains those facts too. Its numeric program check is `supported` with `actual_value = 1.89`.

However, the model also emits an `other` subclaim for “Reporting entity is Amazon for fiscal Q3 2026.” That check is `unchecked_other_claim`. The [claim aggregation rule](../../../src/claimcheck/checks.py) returns `insufficient_evidence` unless all subchecks are supported (or a contradiction dominates). Therefore this example is scored wrong for the supported gold assertion even though the number was transcribed correctly. It is an observed schema/aggregation interaction, not evidence that MP3 recognition lost the number.

Improvement hypothesis: give entity and period metadata explicit, evidence-validated fields, while keeping meaningful nonnumeric qualifications as separately checkable claims. Add tests for an actually wrong company, wrong period and uncheckable qualifier before changing aggregation. Do **not** solve this by ignoring every `other` check or converting every numeric match into overall support.

## How to interpret the controlled formats

Identical prepared text is reused by exact hash within a provider/profile. A reused result is not another independent model observation. Conversely, small OCR/ASR wording differences can cause different extraction and subclaim structures even when financial numbers survive. Compare the prepared text, extracted claim and program checks before assigning a failure to a file format or media model.

The synthetic MP4 contains a static financial card and synthetic speech. Its success cannot establish performance on a real moving video, a long earnings call, speaker identification or image authenticity. Three real Tesla slide pages remain diagnostic examples without complete independently reviewed gold.

## Fixed extraction output limits can produce a complete document miss

In [Meta / INTC / WAV](test/meta/low/INTC-wav/ingest.json), the extraction request returns `incomplete` with `reason = max_output_tokens`. The [raw trace](text-cache/meta/882a6a68aa1349ac70ba6b18bbb22d36009fcb211019a6d9fdb08abd9c0b5ece/traces/20261030T210959Z-f85430b9.json) records 4,000 output tokens, including 3,998 reasoning tokens, under the selected low-verification-reasoning profile. The frozen short-input extractor does not inherit that verification setting: its request has no explicit reasoning override. No extracted claims were returned, so all four preregistered assertions remain wrong. This is not four independently observed wrong financial answers.

The prepared synthetic-audio transcript also contains repeated words. That observation does not establish that repetitions caused the token exhaustion. A future development study should compare bounded extraction windows, output allowances and supported reasoning controls, then use a new held-out set. This run keeps its original fixed cap and incomplete response; it does not replace the failed result with a larger-cap retry or describe two searched profiles as the model's global best performance.

## A rejected quotation is not a successful abstention

In [Baseten / TSLA / WAV](test/baseten/low/TSLA-wav/ingest.json), the future-period revenue assertion is extracted but rejected because its quote is not an exact span of the source text. Its status is `rejected` with no final verdict. Even though the gold label is `insufficient_evidence`, the scorer records `unresolved` and counts a miss; a failed quotation check must not accidentally earn credit for an evidence-based abstention.

The protection is useful: the product refuses a quotation it cannot trace to the input. Improvement should focus on producing and validating exact source spans while preserving the original text. Silently accepting approximate quotations, especially changed numbers, signs, units or periods, would weaken the evidence chain.
