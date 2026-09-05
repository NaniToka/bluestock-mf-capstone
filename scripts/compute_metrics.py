"""
compute_metrics.py
------------------
Computes performance metrics from real dataset.
Primary source: fact_performance (pre-computed alpha/beta/sharpe from real data),
supplemented with NAV-derived CAGR, max-drawdown, volatility.
Outputs fund_scorecard.csv and alpha_beta.csv with real fund names.
"""

import warnings
import sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

warnings.filterwarnings("ignore")

DB      = Path("data/db/bluestock_mf.db")
PROC    = Path("data/processed")
CHARTS  = Path("reports/charts")
CHARTS.mkdir(parents=True, exist_ok=True)

RF_ANNUAL = 0.065
RF_DAILY  = RF_ANNUAL / 252

conn = sqlite3.connect(DB)
nav_df   = pd.read_sql("SELECT * FROM fact_nav",         conn, parse_dates=["date"])
perf_df  = pd.read_sql("SELECT * FROM fact_performance", conn)
fund_df  = pd.read_sql("SELECT * FROM dim_fund",         conn)
bm_df    = pd.read_sql("SELECT * FROM fact_benchmark",   conn, parse_dates=["date"])
conn.close()

nav_pivot  = nav_df.pivot_table(index="date", columns="amfi_code", values="nav").sort_index()
ret_pivot  = nav_pivot.pct_change().dropna(how="all")

nifty50 = (bm_df[bm_df["index_name"] == "NIFTY50"]
           .set_index("date")["close_value"]
           .pct_change().dropna())


def cagr(nav_series, years):
    s = nav_series.dropna()
    if len(s) < 2 or years <= 0: return np.nan
    return (s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1


def max_drawdown(nav_series):
    s = nav_series.dropna()
    peak = s.expanding().max()
    return float(((s - peak) / peak).min())


def volatility(ret_series):
    return float(ret_series.dropna().std() * np.sqrt(252))


def tracking_error(fund_ret, bm_ret):
    common = fund_ret.dropna().index.intersection(bm_ret.dropna().index)
    if len(common) < 10: return np.nan
    return float((fund_ret.loc[common] - bm_ret.loc[common]).std() * np.sqrt(252))


print("Computing NAV-derived metrics …")
nav_rows = []
for code in nav_pivot.columns:
    s = nav_pivot[code].dropna()
    r = ret_pivot[code].dropna() if code in ret_pivot.columns else pd.Series(dtype=float)
    total_yrs = (s.index[-1] - s.index[0]).days / 365.25 if len(s) > 1 else 0
    nav_1y = s[s.index >= s.index[-1] - pd.DateOffset(years=1)]
    nav_3y = s[s.index >= s.index[-1] - pd.DateOffset(years=3)]
    nav_rows.append({
        "amfi_code":       code,
        "cagr_full_pct":   round(cagr(s,  total_yrs) * 100, 2) if total_yrs > 0 else np.nan,
        "cagr_1y_nav_pct": round(cagr(nav_1y, 1)     * 100, 2) if len(nav_1y) > 5 else np.nan,
        "cagr_3y_nav_pct": round(cagr(nav_3y, 3)     * 100, 2) if len(nav_3y) > 5 else np.nan,
        "max_drawdown_nav_pct": round(max_drawdown(s) * 100, 2),
        "volatility_ann_pct":  round(volatility(r)   * 100, 2) if len(r) > 5 else np.nan,
        "tracking_error":      round(tracking_error(r, nifty50), 4),
    })
nav_metrics = pd.DataFrame(nav_rows)

# Merge with pre-computed real performance data
# Use return_1yr_pct, sharpe_ratio, sortino_ratio, alpha, beta from real dataset
perf_latest = perf_df.drop_duplicates(subset=["amfi_code"])

merged = (perf_latest
          .merge(nav_metrics, on="amfi_code", how="left"))

# Composite Scorecard (weights: return 30%, sharpe 25%, sortino 20%, drawdown 15%, alpha 10%)
def rank_col(s, asc=True): return s.rank(ascending=asc, method="min")

merged["r_ret"]    = rank_col(merged["return_1yr_pct"], asc=False)
merged["r_sharpe"] = rank_col(merged["sharpe_ratio"],   asc=False)
merged["r_sortino"]= rank_col(merged["sortino_ratio"],  asc=False)
merged["r_dd"]     = rank_col(merged["max_drawdown_pct"], asc=False)  # less negative = better
merged["r_alpha"]  = rank_col(merged["alpha"],          asc=False)
N = len(merged)
merged["composite_score"] = (
    0.30 * (N + 1 - merged["r_ret"])    +
    0.25 * (N + 1 - merged["r_sharpe"]) +
    0.20 * (N + 1 - merged["r_sortino"])+
    0.15 * (N + 1 - merged["r_dd"])     +
    0.10 * (N + 1 - merged["r_alpha"])
).round(2)
merged["overall_rank"] = merged["composite_score"].rank(ascending=False, method="min").astype(int)
merged = merged.sort_values("overall_rank")

# Scorecard
sc_cols = ["overall_rank","amfi_code","scheme_name","fund_house","category","plan",
           "return_1yr_pct","return_3yr_pct","return_5yr_pct",
           "sharpe_ratio","sortino_ratio","max_drawdown_pct",
           "std_dev_ann_pct","aum_crore","alpha","composite_score"]
scorecard = merged[sc_cols].copy()
scorecard.to_csv(PROC / "fund_scorecard.csv", index=False)

# Alpha / Beta
ab_cols = ["amfi_code","scheme_name","fund_house","category","alpha","beta",
           "sharpe_ratio","sortino_ratio","morningstar_rating","risk_grade"]
alpha_beta = merged[ab_cols].copy()
alpha_beta.to_csv(PROC / "alpha_beta.csv", index=False)

print(f"\n--- Fund Scorecard (Top 10) ---")
print(scorecard[["overall_rank","scheme_name","return_1yr_pct","sharpe_ratio",
                  "max_drawdown_pct","composite_score"]].head(10).to_string(index=False))

# ── Chart 16: Scorecard Heatmap ───────────────────────────────────────────────
heat_cols = ["return_1yr_pct","return_3yr_pct","sharpe_ratio","sortino_ratio","max_drawdown_pct"]
heat = scorecard.set_index("amfi_code")[heat_cols]
fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(heat.T, annot=True, fmt=".2f", cmap="RdYlGn",
            linewidths=0.4, ax=ax, center=0,
            yticklabels=heat_cols,
            xticklabels=[str(c) for c in heat.index])
ax.set_title("Fund Performance Scorecard Heatmap (Real Data)", fontsize=13)
plt.tight_layout()
plt.savefig(CHARTS / "16_scorecard_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Chart 17: Max Drawdown ────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
colors = ["crimson" if v < -25 else "darkorange" if v < -15 else "steelblue"
          for v in scorecard["max_drawdown_pct"]]
ax.barh([s[:35] for s in scorecard["scheme_name"]], scorecard["max_drawdown_pct"], color=colors)
ax.set_title("Maximum Drawdown by Scheme (Real Data)", fontsize=13)
ax.set_xlabel("Max Drawdown (%)")
plt.tight_layout()
plt.savefig(CHARTS / "17_max_drawdown.png", dpi=150, bbox_inches="tight")
plt.close()

# ── Chart 18: Alpha vs Tracking Error ────────────────────────────────────────
te_data = merged[["scheme_name","alpha","tracking_error","category"]].dropna()
fig, ax = plt.subplots(figsize=(10, 6))
cats = te_data["category"].unique()
palette = sns.color_palette("Set1", len(cats))
for cat, col in zip(cats, palette):
    sub = te_data[te_data.category == cat]
    ax.scatter(sub["tracking_error"], sub["alpha"], s=90, c=[col], label=cat, alpha=0.8)
ax.axhline(0, color="gray", linestyle="--", lw=0.8)
ax.set_title("Alpha vs Tracking Error (Real Data)", fontsize=13)
ax.set_xlabel("Tracking Error (ann.)")
ax.set_ylabel("Alpha")
ax.legend()
plt.tight_layout()
plt.savefig(CHARTS / "18_tracking_error.png", dpi=150, bbox_inches="tight")
plt.close()

assert (PROC / "fund_scorecard.csv").exists()
assert (PROC / "alpha_beta.csv").exists()
assert scorecard["fund_house"].str.contains("SBI|HDFC").any(), \
    "Real fund names not in scorecard!"
print(f"\n✅ fund_scorecard.csv and alpha_beta.csv saved with real fund names.")
print("✅ Charts 16–18 saved.")
