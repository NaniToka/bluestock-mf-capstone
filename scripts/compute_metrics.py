"""
compute_metrics.py
------------------
Computes fund performance metrics:
  - CAGR (1Y, 3Y, 5Y from NAV)
  - Sharpe Ratio (Rf = 6.5%)
  - Sortino Ratio
  - Alpha / Beta (OLS vs benchmark)
  - Maximum Drawdown
  - Weighted composite scorecard

Outputs:
  data/processed/fund_scorecard.csv
  data/processed/alpha_beta.csv
  reports/charts/16_scorecard_heatmap.png
  reports/charts/17_max_drawdown.png
  reports/charts/18_tracking_error.png
"""

import warnings
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from pathlib import Path

warnings.filterwarnings('ignore')

DB      = Path("data/db/bluestock_mf.db")
PROC    = Path("data/processed")
CHARTS  = Path("reports/charts")
CHARTS.mkdir(parents=True, exist_ok=True)

RF_ANNUAL = 0.065   # Risk-free rate 6.5%
RF_DAILY  = RF_ANNUAL / 252

conn = sqlite3.connect(DB)

nav_df  = pd.read_sql("SELECT * FROM fact_nav",    conn, parse_dates=["date"])
fund_df = pd.read_sql("SELECT * FROM dim_fund",    conn)
bm_df   = pd.read_sql("SELECT * FROM fact_benchmark", conn, parse_dates=["date"])
conn.close()

# ── Pivot NAV to wide ──────────────────────────────────────────────────────────
nav_pivot = nav_df.pivot_table(index="date", columns="fund_id", values="nav").sort_index()
ret_pivot = nav_pivot.pct_change().dropna(how="all")   # daily returns

# ── Benchmark daily returns (Nifty 100) ───────────────────────────────────────
nifty_ret = (bm_df[bm_df["benchmark"] == "Nifty 100"]
             .set_index("date")["daily_return_pct"] / 100).sort_index()
nifty_ret.index = pd.to_datetime(nifty_ret.index)


# ─────────────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────────────
def cagr(nav_series: pd.Series, years: float) -> float:
    """Compute CAGR over `years` years."""
    if len(nav_series) < 2:
        return np.nan
    start = nav_series.dropna().iloc[0]
    end   = nav_series.dropna().iloc[-1]
    if start <= 0:
        return np.nan
    return (end / start) ** (1 / years) - 1


def sharpe(ret_series: pd.Series) -> float:
    """Annualised Sharpe ratio."""
    excess = ret_series - RF_DAILY
    if excess.std() == 0:
        return np.nan
    return float((excess.mean() / excess.std()) * np.sqrt(252))


def sortino(ret_series: pd.Series) -> float:
    """Annualised Sortino ratio (downside deviation only)."""
    excess   = ret_series - RF_DAILY
    downside = excess[excess < 0]
    if len(downside) == 0 or downside.std() == 0:
        return np.nan
    return float((excess.mean() / downside.std()) * np.sqrt(252))


def max_drawdown(nav_series: pd.Series) -> float:
    """Maximum peak-to-trough drawdown."""
    nav = nav_series.dropna()
    peak = nav.expanding().max()
    dd   = (nav - peak) / peak
    return float(dd.min())


def alpha_beta_ols(fund_ret: pd.Series, bm_ret: pd.Series) -> tuple[float, float, float]:
    """OLS regression: fund_ret = alpha + beta * bm_ret. Returns (alpha_ann, beta, r2)."""
    common = fund_ret.dropna().index.intersection(bm_ret.dropna().index)
    if len(common) < 30:
        return np.nan, np.nan, np.nan
    x = bm_ret.loc[common].values
    y = fund_ret.loc[common].values
    slope, intercept, r, _, _ = stats.linregress(x, y)
    alpha_ann = intercept * 252
    return round(float(alpha_ann), 4), round(float(slope), 4), round(float(r**2), 4)


def tracking_error(fund_ret: pd.Series, bm_ret: pd.Series) -> float:
    """Annualised tracking error."""
    common = fund_ret.dropna().index.intersection(bm_ret.dropna().index)
    if len(common) < 10:
        return np.nan
    diff = fund_ret.loc[common] - bm_ret.loc[common]
    return float(diff.std() * np.sqrt(252))


# ─────────────────────────────────────────────────────────────────────────────
# Compute all metrics
# ─────────────────────────────────────────────────────────────────────────────
print("Computing performance metrics …")

metrics_rows = []
ab_rows      = []

for fid in nav_pivot.columns:
    nav_s = nav_pivot[fid].dropna()
    ret_s = ret_pivot[fid].dropna() if fid in ret_pivot.columns else pd.Series(dtype=float)

    total_years = (nav_s.index[-1] - nav_s.index[0]).days / 365.25 if len(nav_s) > 1 else 0

    # CAGR
    cagr_full = cagr(nav_s, total_years) if total_years > 0 else np.nan
    nav_1y = nav_s[nav_s.index >= nav_s.index[-1] - pd.DateOffset(years=1)]
    nav_3y = nav_s[nav_s.index >= nav_s.index[-1] - pd.DateOffset(years=3)]
    cagr_1y = cagr(nav_1y, 1)   if len(nav_1y) > 5 else np.nan
    cagr_3y = cagr(nav_3y, 3)   if len(nav_3y) > 5 else np.nan

    # Risk metrics
    sh  = sharpe(ret_s)
    so  = sortino(ret_s)
    mdd = max_drawdown(nav_s)
    vol = float(ret_s.std() * np.sqrt(252)) if len(ret_s) > 1 else np.nan
    te  = tracking_error(ret_s, nifty_ret)

    # Alpha / Beta
    alpha, beta, r2 = alpha_beta_ols(ret_s, nifty_ret)

    row = {
        "fund_id":       fid,
        "cagr_full_pct": round(cagr_full * 100, 2) if not np.isnan(cagr_full) else np.nan,
        "cagr_1y_pct":   round(cagr_1y   * 100, 2) if not np.isnan(cagr_1y)   else np.nan,
        "cagr_3y_pct":   round(cagr_3y   * 100, 2) if not np.isnan(cagr_3y)   else np.nan,
        "sharpe":        round(sh,  3) if not np.isnan(sh)  else np.nan,
        "sortino":       round(so,  3) if not np.isnan(so)  else np.nan,
        "max_drawdown_pct": round(mdd * 100, 2) if not np.isnan(mdd) else np.nan,
        "volatility_ann_pct": round(vol * 100, 2) if not np.isnan(vol) else np.nan,
        "tracking_error": round(te, 4) if not np.isnan(te) else np.nan,
    }
    metrics_rows.append(row)

    ab_rows.append({
        "fund_id":    fid,
        "alpha_ann":  alpha,
        "beta":       beta,
        "r_squared":  r2,
    })

metrics_df = pd.DataFrame(metrics_rows).merge(fund_df[["fund_id","scheme_name","category"]], on="fund_id")
ab_df      = pd.DataFrame(ab_rows).merge(fund_df[["fund_id","scheme_name","category"]], on="fund_id")

# ─────────────────────────────────────────────────────────────────────────────
# Composite Scorecard
# ─────────────────────────────────────────────────────────────────────────────
# Weights: CAGR_1Y 30%, Sharpe 25%, Sortino 20%, Max DD 15% (inverted), Alpha 10%
def rank_col(series, ascending=True):
    """Rank 1=best. ascending=True → lower value is better."""
    return series.rank(ascending=ascending, method="min")

sc = metrics_df.copy()
sc["r_cagr_1y"]  = rank_col(sc["cagr_1y_pct"],      ascending=False)
sc["r_sharpe"]   = rank_col(sc["sharpe"],            ascending=False)
sc["r_sortino"]  = rank_col(sc["sortino"],           ascending=False)
sc["r_mdd"]      = rank_col(sc["max_drawdown_pct"],  ascending=True)   # less negative = better
ab_merged = sc.merge(ab_df[["fund_id","alpha_ann"]], on="fund_id")
ab_merged["r_alpha"] = rank_col(ab_merged["alpha_ann"], ascending=False)

ab_merged["composite_score"] = (
    0.30 * (11 - ab_merged["r_cagr_1y"]) +
    0.25 * (11 - ab_merged["r_sharpe"])  +
    0.20 * (11 - ab_merged["r_sortino"]) +
    0.15 * (11 - ab_merged["r_mdd"])     +
    0.10 * (11 - ab_merged["r_alpha"])
)
ab_merged["composite_score"] = ab_merged["composite_score"].round(2)
ab_merged["overall_rank"]    = ab_merged["composite_score"].rank(ascending=False, method="min").astype(int)

scorecard = ab_merged.sort_values("overall_rank")
scorecard_cols = ["overall_rank","fund_id","scheme_name","category",
                  "cagr_1y_pct","cagr_3y_pct","sharpe","sortino",
                  "max_drawdown_pct","volatility_ann_pct","alpha_ann","composite_score"]
scorecard[scorecard_cols].to_csv(PROC / "fund_scorecard.csv", index=False)
ab_df.to_csv(PROC / "alpha_beta.csv", index=False)
print(f"  ✔ fund_scorecard.csv saved  ({len(scorecard)} rows)")
print(f"  ✔ alpha_beta.csv saved  ({len(ab_df)} rows)")

print("\n--- Fund Scorecard ---")
print(scorecard[["overall_rank","fund_id","scheme_name","cagr_1y_pct","sharpe","sortino",
                  "max_drawdown_pct","composite_score"]].to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# Chart 16: Scorecard Heatmap
# ─────────────────────────────────────────────────────────────────────────────
heat_cols = ["cagr_1y_pct","cagr_3y_pct","sharpe","sortino","max_drawdown_pct","volatility_ann_pct"]
heat_data = scorecard.set_index("fund_id")[heat_cols]

fig, ax = plt.subplots(figsize=(12, 6))
sns.heatmap(heat_data.T, annot=True, fmt=".2f", cmap="RdYlGn",
            linewidths=0.5, ax=ax, center=0)
ax.set_title("Fund Performance Scorecard Heatmap", fontsize=13)
ax.set_xlabel("Fund ID")
ax.set_ylabel("Metric")
plt.tight_layout()
plt.savefig(CHARTS / "16_scorecard_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Chart 16 saved.")

# ─────────────────────────────────────────────────────────────────────────────
# Chart 17: Max Drawdown
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5))
colors = ["crimson" if v < -20 else "darkorange" if v < -10 else "steelblue"
          for v in scorecard["max_drawdown_pct"]]
bars = ax.barh(scorecard["fund_id"], scorecard["max_drawdown_pct"], color=colors)
ax.set_title("Maximum Drawdown by Fund (%)", fontsize=13)
ax.set_xlabel("Max Drawdown (%)")
ax.axvline(0, color="black", lw=0.5)
for bar, val in zip(bars, scorecard["max_drawdown_pct"]):
    ax.text(val - 0.5, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}%", va="center", ha="right", fontsize=8, color="white")
plt.tight_layout()
plt.savefig(CHARTS / "17_max_drawdown.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Chart 17 saved.")

# ─────────────────────────────────────────────────────────────────────────────
# Chart 18: Tracking Error vs Alpha
# ─────────────────────────────────────────────────────────────────────────────
te_data = scorecard.copy()
# alpha_ann already present in scorecard from the ab_merged join above
# add beta from ab_df
te_data = te_data.merge(ab_df[["fund_id","beta"]], on="fund_id")
fig, ax = plt.subplots(figsize=(9, 6))
ax.scatter(te_data["tracking_error"], te_data["alpha_ann"] * 100,
           s=100, c="steelblue", alpha=0.8, edgecolors="white", linewidth=0.8)
for _, r in te_data.iterrows():
    ax.annotate(r["fund_id"], (r["tracking_error"], r["alpha_ann"]*100),
                textcoords="offset points", xytext=(5, 3), fontsize=8)
ax.axhline(0, color="gray", linestyle="--", lw=0.8)
ax.set_title("Tracking Error vs Alpha (Active Risk vs Active Return)", fontsize=13)
ax.set_xlabel("Tracking Error (annualised)")
ax.set_ylabel("Alpha (% per year)")
plt.tight_layout()
plt.savefig(CHARTS / "18_tracking_error.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Chart 18 saved.")

# assertions
assert (PROC / "fund_scorecard.csv").exists(), "fund_scorecard.csv not found"
assert (PROC / "alpha_beta.csv").exists(),     "alpha_beta.csv not found"
print("\n✅ Performance metrics complete. All assertions passed.")
