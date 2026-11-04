# Evidence index

The headline is **240/266 (90.2%) held-out text accuracy**, false support **1/139** reference contradicted/insufficient claims, on Baseten Muse Spark Open. Corrected gold; failures count as wrong. Coverage ≠ accuracy.

| Inspect | Evidence and limits |
| --- | --- |
| Original benchmark | [Report](eval-v2-2026-10-27/REPORT.md#metrics), [registered-gold scores](eval-v2-2026-10-27/REPORT-registered-gold.md), [manifest](eval-v2-2026-10-27/manifest.json) (dirty working tree). 357 total = 91 dev + 266 held out. Full-set 323/357 (90.5%) is a historical all-claim result, not the held-out headline. |
| Every saved verdict | [Explorer](../explorer/index.html), [data](../explorer/data.json); incomplete/provider-error results count as wrong. |
| Live production, 2026-11-03 | [Receipt](live-prod-2026-11-03/REPORT.md): unauthorized on wrong password; supported Apple check, Baseten, $0.00988, 6.34 s; $3/day budget decremented. Owner-supplied checks; no new paid execution for this IA change. |
| Real-world posts | [In the wild](../wild/index.html), [80 News / 78 Threads inputs](real-world-2026-11-02/REPORT.md); coverage, abstention and primary truth labels are separate. Coverage ≠ accuracy. |
| Post-hoc text rechecks | [News and Threads fix recheck](real-world-2026-11-03-fixcheck/REPORT.md), [v2 agent rerun](eval-v2-2026-10-28-r2-posthoc/REPORT.md); previously seen inputs, not held out; no OCR/ASR retest. Empty single-shot rows are not results. |
| Saved examples, animation, charts, methodology | [Site evidence tour](site-tour/index.html): retained stamp scene, input boundaries, post examples, all-claim results and trust explanation. |
| Extended judge review | [Criteria, media studies, corrected gold and historical failure review](REVIEW_GUIDE.md). |
| Technical reference and CLI | [English](TECHNICAL_GUIDE.md), [繁體中文](TECHNICAL_GUIDE.zh-TW.md): setup, commands, architecture, responsibilities and source policy. |
| Media and releases | [Controlled formats](fair-multimodal-v1/REPORT.md), [real AV](real-av-context-live/REPORT.md), [Tesla follow-ups](stock-context-posthoc-2026-10-30/REPORT.md), [L4 development claims](eval-l4-2026-10-29/ANALYSIS.md); retain their extraction, sampling and post-hoc labels. |
| LoRA attempt | [Report](lora-2026-11-03/REPORT.md): tokenizer access blocked training; no trained adapter or improvement claim. |
| Verification and retained attempts | [Offline entry point](../../AGENTS.md), [test-record policy](../TEST_RECORDS.md), [IA validation](../serving-checks/simplify-20261103/README.md). |

[Judge guide](../../JUDGES.md) · [README](../../README.md) · [Build disclosure](../../BUILD_LOG.md#build-log) · [Credits](../../CREDITS.md) · [License](../../LICENSE).
