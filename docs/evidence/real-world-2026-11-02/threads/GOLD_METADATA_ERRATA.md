# Source-tier metadata correction

The pre-call frozen builder incorrectly labelled every companyfacts value L1, including quarterly 10-Q facts, and labelled calculated growth L1. This is a metadata error against the repository's [source policy](../../../DATA_SOURCES.md#sec-evidence-tiers). The original gold, sources, builder and FREEZE remain byte-identical. Numeric values, periods, arithmetic, verdict labels, cases, scoring denominators and paid inputs are unchanged. No provider output was used to select or change a truth label.

The [corrected metadata copy](gold-source-tiers-corrected.jsonl) is reproducible offline. Source `form` fields establish the distinction: audited annual 10-K values L1; reviewed quarterly 10-Q values L2; growth derived from two facts L3; furnished earnings releases L4. The companyfacts container itself has no single evidence tier.

Original frozen gold SHA-256: `4d0c22298c97b3e42c61a326ccd037fcf2ee3548895184a38d03d283b9c65461`.

| Case | Corrected component tiers | Meaning |
|---|---|---|
| T19 | L2, L4 | FY2026 Q2 revenue: L2; year-over-year revenue growth: L4; non-GAAP diluted EPS: L4; Data Center segment revenue: L4; Q3 2026 revenue guidance midpoint; statement, not forecast realization: L4 |
| T02 | L2, L3 | Q3 2026 revenue: L2; year-over-year revenue growth: L3 |
| T09 | L2, L4 | FY2027 Q1 revenue: L2; year-over-year revenue growth: L4; adjusted diluted EPS: L4 |
| T03 | L1, L2 | 2023 annual revenue: L1; 2024 annual revenue: L1; 2025 annual revenue: L1; 2026 Q1 revenue: L2 |
| T33 | L4 | FY2026 Q4 revenue: L4; year-over-year revenue growth: L4; diluted EPS: L4; FY2026 Q4 iPhone revenue: L4; FY2026 Q4 Greater China revenue: L4 |

Registered while the agent pass was still running, before the post pass; this correction does not claim a second independent gold review. Accuracy continues to use the unchanged frozen verdict labels. See SCORING_NOTE.json for compound-item metrics.
