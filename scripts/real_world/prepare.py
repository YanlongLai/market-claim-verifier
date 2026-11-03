"""Human-screened paraphrases tied to the frozen published snapshot.

Indices refer only to the cached, seeded screening inventory, not gold/results.
The resulting public files contain paraphrases and provenance, never feed text.
"""
from __future__ import annotations

import json
from pathlib import Path
from collect import sample, screening_inventory

# Screening completed before gold construction and before all model execution.
# (candidate index, claim type, independently written short paraphrase)
FINANCIAL = [
    (0, "analyst_forecast", "The estimate for Nvidia's fiscal 2028 revenue has increased by 25% since June."),
    (1, "analyst_forecast", "A discussion post estimates Wiwynn's 2027 revenue at TWD 2.5 trillion."),
    (3, "margin", "Airbnb has a net profit margin of 20%."),
    (4, "growth", "Powerchip Semiconductor Manufacturing's Q3 revenue increased by 80%."),
    (6, "guidance", "UnitedHealth raised its 2026 adjusted EPS outlook to at least $20.50."),
    (7, "analyst_forecast", "Analysts estimate Novatek's third-quarter EPS at about TWD 9.5."),
    (8, "revenue", "TSMC generated $46.7 billion of revenue in its latest quarter."),
    (11, "margin", "Lite-On Technology's most recent gross margin reached 25.9%."),
    (12, "revenue", "Compal's Q3 revenue exceeded TWD 240 billion."),
    (13, "growth", "Intuitive Surgical's revenue increased by 22%."),
    (14, "net_income", "Shell's Q3 2026 net income was $12.1 billion."),
    (15, "growth", "Winbond's September revenue increased by 256% from a year earlier."),
    (16, "guidance", "Compeq aims for AI and satellite products to generate more than half of next year's revenue."),
    (17, "segment_kpi", "SpaceX's Q3 AI revenue exceeded $7.6 billion."),
    (18, "eps", "AUO posted a third-quarter loss of TWD 0.33 per share."),
    (19, "growth", "Realtek's 2026 Q3 revenue increased by 28% year over year."),
    (22, "eps", "Lite-On Technology's third-quarter EPS reached TWD 3.27."),
    (23, "revenue", "Ares Capital's Q3 2026 investment income was $763 million."),
    (25, "analyst_forecast", "An investment adviser projects MediaTek's 2027 ASIC revenue at $16 billion."),
    (26, "guidance", "MediaTek's ASIC revenue is expected to reach $2.5 billion in the fourth quarter."),
    (27, "eps", "Kinsus reported EPS of TWD 8.38 for January through September of ROC year 115."),
    (28, "revenue", "Inventec's Q3 revenue was TWD 272 billion."),
    (29, "growth", "MediaTek's 2026 Q3 revenue rose by 18% year over year."),
    (30, "segment_kpi", "Starbucks' US comparable-store sales grew by 7.7% last quarter."),
    (33, "revenue", "Anthropic's third-quarter revenue was nearly $17 billion."),
    (34, "segment_kpi", "TSMC's 2-nanometer process accounts for 8% of wafer revenue."),
    (36, "analyst_forecast", "Analyst estimates imply AMD's net income will grow by 501% over four years."),
    (39, "growth", "Costco's September net sales increased by 13%."),
    (40, "analyst_forecast", "Novatek's full-year EPS is forecast at TWD 34.9."),
    (41, "eps", "Hon Precision's EPS for the first three quarters was TWD 93.47."),
    (42, "revenue", "PharmaEssentia's August revenue was TWD 2.617 billion."),
    (44, "segment_kpi", "Advanced packaging now represents 30% of Powertech Technology's revenue."),
    (45, "growth", "Hon Precision's 2026 Q3 revenue increased by 98% year over year."),
    (47, "cash_flow", "Airbnb generated $4.6 billion of free cash flow."),
    (48, "eps", "UnitedHealth's adjusted EPS increased to $4.69."),
    (49, "non_gaap_eps", "Ares Capital reported third-quarter Core Earnings of $0.46 per share."),
    (52, "margin", "Booking has a net profit margin of 20%."),
    (54, "segment_kpi", "Broadcom's AI semiconductor revenue increased by 221%."),
    (56, "margin", "Airbnb's net profit margin is 20%."),
    (58, "margin", "Alibaba's net profit margin is 10%."),
    (61, "segment_kpi", "Starbucks' US comparable-store sales increased by 7.7% in fiscal Q4 2026."),
    (62, "analyst_forecast", "Analysts expect AMD's 2027 EPS to be more than twice its previous level."),
    (63, "growth", "Five Below's revenue increased by 23%."),
    (64, "margin", "Starbucks' operating margin expanded to 14%."),
    (65, "relative_revenue", "Coupang's revenue is between 2.5 and 3 times Airbnb's revenue."),
    (66, "segment_kpi", "Chipotle's third-quarter comparable sales increased by 2.1%."),
]
EXTRA = [
    (4, "segment_kpi", "AWS grew by 39% last quarter."),
    (9, "segment_kpi", "PCs contributed 19% of Dell's segment profit last quarter."),
    (28, "non_gaap_income", "Shell's third-quarter adjusted earnings were approximately $10.8 billion."),
    (29, "net_income", "Shell's profit rose to $10.8 billion."),
    (34, "analyst_forecast", "Analysts expect Formosa Petrochemical's EPS to increase by 780%."),
    (35, "eps", "Taiwan Glass earned TWD 1.57 per share during the first three quarters."),
    (36, "eps", "Lite-On Technology's third-quarter EPS was TWD 3.28."),
    (39, "analyst_forecast", "The FactSet consensus estimate for Chroma's EPS was raised to TWD 48.3."),
    (40, "analyst_forecast", "The FactSet consensus estimate for Realtek's EPS was increased to TWD 32.5."),
    (41, "analyst_forecast", "Elite Material's EPS is expected to reach TWD 71.44 next year."),
    (44, "analyst_forecast", "The FactSet consensus estimate for EVA Air's EPS was increased to TWD 4.22."),
    (47, "analyst_forecast", "The FactSet consensus EPS forecast for Kinsus was raised to TWD 12.77."),
    (48, "analyst_forecast", "The FactSet consensus estimate for Global Unichip's EPS was raised to TWD 56.51."),
    (51, "eps", "Hon Precision reported EPS of TWD 93.47 for the first three quarters."),
]

CONTROLS = [
    (0, "price_move", "Syntec shares recovered to TWD 2,000."),
    (1, "price_move", "Taiwan's stock index was down 428 points after several large stocks recovered."),
    (3, "ownership_trade", "Summit Global Investments sold 10,949 Shell ADR shares."),
    (5, "corporate_event", "Mega Financial received a silver national corporate environmental award."),
    (6, "market_share", "Hotai Motor captured almost 40% of October's car market."),
    (7, "opinion", "A hypothetical Tesla merger calculation assigns values as high as $813 per share."),
    (8, "price_move", "Unimicron shares recovered above TWD 1,000 during the trading session."),
    (9, "price_move", "Yuanta Financial shares declined for two consecutive sessions."),
    (10, "price_move", "Taiwan's stock index fell by more than 1,400 points during the session."),
    (11, "opinion", "A commentary questions whether Taishin and Shin Kong's combined earnings can justify their merged scale."),
    (13, "opinion", "Amazon's backing may give X-Energy an advantage over Oklo."),
    (14, "price_move", "KGI Financial shares declined by 7.07% to TWD 25.65 during trading."),
    (15, "price_move", "Shanghai Commercial and Savings Bank shares edged higher."),
    (16, "corporate_event", "Airtac was invited to an online investor meeting organized by UBS."),
    (17, "opinion", "A commentator recommends buying Apple despite its latest MacBook offering little change."),
    (18, "opinion", "A market comment expresses hope for Wiwynn shares to recover."),
    (19, "price_move", "Taiwan Specialty Chemical shares declined by 3.39%."),
    (20, "price_move", "Fulltech Fiber Glass shares reversed early losses and reached the daily upper limit."),
    (21, "opinion", "A report describes foreign investors looking for inexpensive stocks after AI shares declined."),
    (22, "price_move", "Tongtai shares gained 39% over six days."),
]


def metadata(row: dict) -> dict:
    return {key: row[key] for key in ("market", "outlet", "url", "published_at", "ticker", "tickers", "story_sha256")}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows))


def prepare(cache: Path, out: Path) -> None:
    if (out / "FREEZE.json").exists():
        raise RuntimeError("frozen input files must never be replaced")
    inventory = json.loads((cache / "inventory.json").read_text())
    candidates, extra = screening_inventory(inventory)
    eligible = []
    for records, annotations in ((candidates, FINANCIAL), (extra, EXTRA)):
        for index, kind, claim in annotations:
            eligible.append({**records[index], "claim_type": kind, "claim": claim, "screen": "numeric_financial"})
    financial = sample(eligible, 70)
    selected = {row["url"] for row in eligible}
    controls = sample([row for row in inventory if row["url"] not in selected], len(inventory))
    (cache / "control-candidates.json").write_text(json.dumps(controls, ensure_ascii=False, indent=2))
    public = [{**metadata(row), "claim": row["claim"], "claim_type": row["claim_type"], "sample_group": row["screen"]} for row in financial]
    for i, row in enumerate(public, 1):
        row["id"] = f"RW{i:03d}"
    write_jsonl(out / "claims-financial.jsonl", public)
    for index, kind, claim in CONTROLS:
        public.append({**metadata(controls[index]), "id": f"RW{len(public) + 1:03d}",
                       "claim": claim, "claim_type": kind, "sample_group": "support_control"})
    write_jsonl(out / "claims.jsonl", public)
    screen = []
    for row in candidates + extra:
        screen.append({**metadata(row), "selected_financial": row["url"] in selected,
                       "reason": "numeric financial statement" if row["url"] in selected else "no complete numerical financial assertion in displayed title/summary, or metric outside requested screen"})
    write_jsonl(out / "screening.jsonl", screen)
    print(f"eligible financial stories: {len(eligible)}; total selected including controls: {len(public)}")
    print(f"non-financial controls: {len(CONTROLS)}; excluded control ranks 2,4,12 (investment plan, unnamed EPS forecast, ticker page)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.cache, args.out)
