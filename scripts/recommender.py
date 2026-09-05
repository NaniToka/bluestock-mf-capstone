"""
recommender.py
--------------
Risk-appetite based fund recommender.
Maps investor risk_profile → recommended fund categories → top funds by composite score.
"""

import pandas as pd
from pathlib import Path

PROC = Path("data/processed")

RISK_MAP = {
    "Conservative": ["Debt", "Hybrid"],
    "Moderate":     ["Hybrid", "Equity"],
    "Aggressive":   ["Equity"],
}


def recommend(risk_profile: str, top_n: int = 3) -> pd.DataFrame:
    """Return top_n recommended funds for a given risk profile."""
    scorecard = pd.read_csv(PROC / "fund_scorecard.csv")
    categories = RISK_MAP.get(risk_profile, ["Hybrid"])
    filtered = scorecard[scorecard["category"].isin(categories)]
    return filtered.sort_values("composite_score", ascending=False).head(top_n)[
        ["overall_rank", "amfi_code", "scheme_name", "category",
         "return_1yr_pct", "sharpe_ratio", "composite_score"]
    ].reset_index(drop=True)


if __name__ == "__main__":
    print("=" * 60)
    print("  Bluestock MF – Fund Recommender")
    print("=" * 60)
    for profile in ["Conservative", "Moderate", "Aggressive"]:
        print(f"\n  Risk Profile: {profile}")
        recs = recommend(profile)
        print(recs.to_string(index=False))
    print("\n✅ Recommender complete.")
