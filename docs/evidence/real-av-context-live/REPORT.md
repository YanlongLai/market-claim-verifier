# Context-bound real AV: live verification results

Same six retained claim inputs across three providers: four GAAP table values, event-bound revenue/growth, and an unchanged missing-period adjusted-EPS control. This is a **known-failure post-hoc verification**, not held-out accuracy or a fresh audio/video extraction study. No OCR/ASR was repeated.

[Preregistered protocol](PROTOCOL.md) · [Frozen inputs and provenance](cases.json) · [Machine results](summary.json) · [Readable case details](results.html)

| Case | Claim / context | Meta | Baseten | Fireworks |
| --- | --- | --- | --- | --- |
| C01 | Microsoft reported Revenue of $92.3 billion in fiscal Q1 2027. | [failed](meta/C01.json) | [supported](baseten/C01.json) | [supported](fireworks/C01.json) |
| C02 | Microsoft reported Net income of $36.6 billion in fiscal Q1 2027. | [failed](meta/C02.json) | [supported](baseten/C02.json) | [supported](fireworks/C02.json) |
| C03 | Microsoft reported Diluted earnings per share of $4.92 in fiscal Q1 2027. | [failed](meta/C03.json) | [supported](baseten/C03.json) | [supported](fireworks/C03.json) |
| C04 | Microsoft reported Operating income of $45.9 billion in fiscal Q1 2027. | [supported](meta/C04.json) | [supported](baseten/C04.json) | [supported](fireworks/C04.json) |
| C05 | Microsoft reported revenue of $92.3 billion for fiscal Q1 2027, up 19%. | [insufficient_evidence](meta/C05.json) | [supported](baseten/C05.json) | [supported](fireworks/C05.json) |
| C06 | Microsoft reported earnings per share was $4.89 for this quarter, an increase of 18% and 19% in constant currency when adjusted for the impact for its investment in OpenAI. | [insufficient_evidence](meta/C06.json) | [insufficient_evidence](baseten/C06.json) | [insufficient_evidence](fireworks/C06.json) |

Supported means valid program checks within the recorded evidence, period and tolerance. It remains conditional on the reviewed event context. It does not authenticate the speaker, certify the entire video, resolve every table column or validate adjusted EPS. Failures remain failures and are not scored as wrong financial answers. The six cases are not an independent gold accuracy denominator.

## Spend (USD, estimated/reserved)

| Platform | New follow-up | Combined task |
| --- | ---: | ---: |
| meta | 0.30357855 | 4.75379365 |
| baseten | 0.04467450 | 2.20323285 |
| fireworks | 0.06691585 | 2.10332610 |

The latest owner reply sets $30 combined across all three platforms for this round, subject to prior platform credit ceilings; see budget-note.json. The execution caps remained $2 per platform. Failed attempts and unreconciled reservations remain counted. No invoice or account balance is inferred. Original real-AV and admission-replay records are unchanged.

## Reuse

Run `python3 scripts/report_event_context_live.py` for an offline report/audit rebuild. Do not rerun the paid runner to inspect results; it deliberately refuses an existing freeze marker. Every result links its full raw request/response/tool trace. Source code is archived in frozen-source.zip. [Chinese analysis](ANALYSIS.zh-TW.md) describes what improved and what still blocks verification.
