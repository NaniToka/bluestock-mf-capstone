"""
validate.py — dry-run all data queries in dashboard/app.py without Streamlit.
Run: python3 dashboard/validate.py
"""
import sys
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE = Path(__file__).resolve().parent.parent
DB   = BASE / "data" / "db" / "bluestock_mf.db"
PROC = BASE / "data" / "processed"

conn = sqlite3.connect(DB)
funds      = pd.read_sql("SELECT * FROM dim_fund", conn)
investors  = pd.read_sql("SELECT * FROM dim_investor", conn)
nav_df     = pd.read_sql("SELECT * FROM fact_nav", conn)
txn_df     = pd.read_sql("SELECT * FROM fact_transactions", conn)
aum_df     = pd.read_sql("SELECT * FROM fact_aum", conn)
sip_df     = pd.read_sql("SELECT * FROM fact_sip", conn)
perf_df    = pd.read_sql("SELECT * FROM fact_performance", conn)
bm_df      = pd.read_sql("SELECT * FROM fact_benchmark", conn)
hold_df    = pd.read_sql("SELECT * FROM fact_holdings", conn)
scorecard  = pd.read_csv(PROC / "fund_scorecard.csv")
alpha_beta = pd.read_csv(PROC / "alpha_beta.csv")
conn.close()

nav_df["date"]     = pd.to_datetime(nav_df["date"])
txn_df["txn_date"] = pd.to_datetime(txn_df["txn_date"])
bm_df["date"]      = pd.to_datetime(bm_df["date"])
aum_df["month_dt"] = pd.to_datetime(aum_df["month"] + "-01")

errors = []

def check(label, fn):
    try:
        fn()
        print(f"  ✅ {label}")
    except Exception as e:
        errors.append((label, e))
        print(f"  ❌ {label}: {e}")

# PAGE 1
def p1_kpis():
    latest_month = aum_df["month"].max()
    total_aum    = aum_df[aum_df["month"] == latest_month]["aum_cr"].sum()
    sip_inflows  = txn_df[txn_df["txn_type"] == "Sip"]["amount"].sum() / 1e7
    folio_count  = txn_df["folio_no"].nunique()
    scheme_count = funds["fund_id"].nunique()
    print(f"     AUM={total_aum:,.0f} Cr | SIP={sip_inflows:.1f} Cr | Folios={folio_count:,} | Schemes={scheme_count}")

def p1_aum_trend():
    industry = aum_df.groupby("month_dt")["aum_cr"].sum().reset_index()
    assert len(industry) > 0

def p1_aum_amc():
    latest = aum_df["month"].max()
    aum_amc = aum_df[aum_df["month"] == latest].merge(funds[["fund_id","amc"]], on="fund_id")
    assert len(aum_amc) > 0

# PAGE 2
def p2_scatter():
    latest_yr = perf_df["year"].max()
    pp = (perf_df[perf_df["year"] == latest_yr]
          .merge(funds[["fund_id","scheme_name","amc","category"]], on="fund_id")
          .merge(aum_df[aum_df["month"] == aum_df["month"].max()][["fund_id","aum_cr"]],
                 on="fund_id", how="left"))
    assert len(pp) == 10, f"Expected 10, got {len(pp)}"

def p2_scorecard():
    sc = scorecard.merge(funds[["fund_id","amc"]], on="fund_id", how="left")
    assert "overall_rank" in sc.columns

def p2_nav_bm():
    fid = funds["fund_id"].iloc[0]
    fn  = nav_df[nav_df["fund_id"] == fid].sort_values("date")
    fn["idx"] = fn["nav"] / fn["nav"].iloc[0] * 100
    bm50 = bm_df[bm_df["benchmark"] == "Nifty 100"].sort_values("date")
    bm50["idx"] = bm50["index_value"] / bm50["index_value"].iloc[0] * 100
    assert len(fn) > 0 and len(bm50) > 0

# PAGE 3
def p3_city():
    city = (txn_df.groupby("city")["amount"].sum() / 1e7).nlargest(15)
    assert len(city) > 0

def p3_txn_split():
    split = txn_df.groupby("txn_type")["amount"].sum()
    assert len(split) > 0

def p3_age_sip():
    def ab(a): return "18–30" if a<=30 else "31–45" if a<=45 else "46–60" if a<=60 else "60+"
    inv_age = investors[["investor_id","age"]].copy()
    inv_age["age_band"] = inv_age["age"].apply(ab)
    merged = txn_df.merge(inv_age, on="investor_id", how="left")
    sip_age = merged[merged["txn_type"] == "Sip"].groupby("age_band")["amount"].mean()
    assert len(sip_age) > 0

def p3_monthly_vol():
    txn_copy = txn_df.copy()
    txn_copy["month"] = txn_copy["txn_date"].dt.to_period("M").astype(str)
    vol = txn_copy.groupby("month")["amount"].sum() / 1e7
    assert len(vol) > 0

# PAGE 4
def p4_sip_nifty():
    sip_monthly = (txn_df[txn_df["txn_type"] == "Sip"]
                   .groupby("txn_month")["amount"].sum() / 1e7).reset_index()
    sip_monthly.columns = ["month", "sip_cr"]

    nifty_monthly = (bm_df[bm_df["benchmark"] == "Nifty 100"]
                     .assign(month=lambda d: d["date"].dt.to_period("M").astype(str))
                     .groupby("month")["index_value"].last().reset_index())
    merged = sip_monthly.merge(nifty_monthly[["month","index_value"]], on="month", how="inner")
    assert len(merged) > 0, f"merged empty — sip months: {sip_monthly.month.tolist()[:3]}"

def p4_cat_hmap():
    tc = txn_df[txn_df["txn_type"].isin(["Sip","Lumpsum"])].merge(
        funds[["fund_id","category"]], on="fund_id")
    tc["quarter"] = tc["txn_date"].dt.to_period("Q").astype(str)
    pivot = tc.groupby(["category","quarter"])["amount"].sum().unstack(fill_value=0)
    assert pivot.shape[0] > 0

def p4_net_inflow():
    ni = aum_df.merge(funds[["fund_id","category"]], on="fund_id").groupby("category")["net_inflow_cr"].sum()
    assert len(ni) > 0

def p4_rolling():
    sip_monthly = (txn_df[txn_df["txn_type"] == "Sip"]
                   .groupby("txn_month")["amount"].sum() / 1e7).reset_index()
    sip_monthly.columns = ["month", "sip_cr"]
    sip_monthly["month_dt"] = pd.to_datetime(sip_monthly["month"] + "-01")
    roll = sip_monthly.set_index("month_dt")["sip_cr"].rolling(12).sum()
    assert len(roll) > 0

print("=" * 55)
print("  Dashboard Data Validation")
print("=" * 55)

print("\n[Page 1 — Industry Overview]")
check("KPI cards", p1_kpis)
check("AUM trend line", p1_aum_trend)
check("AUM by AMC bar", p1_aum_amc)

print("\n[Page 2 — Fund Performance]")
check("Risk vs return scatter", p2_scatter)
check("Scorecard table", p2_scorecard)
check("NAV vs benchmark", p2_nav_bm)

print("\n[Page 3 — Investor Analytics]")
check("City investment bar", p3_city)
check("Transaction type donut", p3_txn_split)
check("Age group SIP bar", p3_age_sip)
check("Monthly volume line", p3_monthly_vol)

print("\n[Page 4 — SIP & Market Trends]")
check("SIP inflows vs Nifty", p4_sip_nifty)
check("Category heatmap", p4_cat_hmap)
check("Net inflow bar", p4_net_inflow)
check("Rolling SIP momentum", p4_rolling)

print()
if errors:
    print(f"❌ {len(errors)} validation(s) failed:")
    for lbl, err in errors:
        print(f"   • {lbl}: {err}")
    sys.exit(1)
else:
    print("✅ All 15 validations passed — dashboard is ready.")
