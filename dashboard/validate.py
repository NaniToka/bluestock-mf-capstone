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
funds      = funds.rename(columns={"amfi_code": "fund_id", "fund_house": "amc"})
nav_df     = pd.read_sql("SELECT * FROM fact_nav", conn)
nav_df     = nav_df.rename(columns={"amfi_code": "fund_id"})
txn_df     = pd.read_sql("SELECT * FROM fact_transactions", conn)
txn_df     = txn_df.rename(columns={"transaction_date": "txn_date", "amfi_code": "fund_id", "transaction_type": "txn_type", "amount_inr": "amount"})
aum_df     = pd.read_sql("SELECT * FROM fact_aum", conn)
aum_df     = aum_df.rename(columns={"date": "month", "aum_crore": "aum_cr", "fund_house": "amc"})
sip_df     = pd.read_sql("SELECT * FROM fact_sip_inflows", conn)
perf_df    = pd.read_sql("SELECT * FROM fact_performance", conn)
perf_df    = perf_df.rename(columns={"amfi_code": "fund_id", "fund_house": "amc"})
bm_df      = pd.read_sql("SELECT * FROM fact_benchmark", conn)
hold_df    = pd.read_sql("SELECT * FROM fact_holdings", conn)
hold_df    = hold_df.rename(columns={"amfi_code": "fund_id"})
cat_inflows= pd.read_sql("SELECT * FROM fact_category_inflows", conn)
scorecard  = pd.read_csv(PROC / "fund_scorecard.csv")
alpha_beta = pd.read_csv(PROC / "alpha_beta.csv")
conn.close()

nav_df["date"]     = pd.to_datetime(nav_df["date"])
txn_df["txn_date"] = pd.to_datetime(txn_df["txn_date"])
bm_df["date"]      = pd.to_datetime(bm_df["date"])
aum_df["month"]    = pd.to_datetime(aum_df["month"])
aum_df["month_dt"] = aum_df["month"]

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
    sip_inflows  = txn_df[txn_df["txn_type"].str.upper() == "SIP"]["amount"].sum() / 1e7
    folio_count  = txn_df["investor_id"].nunique()
    scheme_count = funds["fund_id"].nunique()
    print(f"     AUM={total_aum:,.0f} Cr | SIP={sip_inflows:.1f} Cr | Folios={folio_count:,} | Schemes={scheme_count}")

def p1_aum_trend():
    industry = aum_df.groupby("month_dt")["aum_cr"].sum().reset_index()
    assert len(industry) > 0

def p1_aum_amc():
    latest = aum_df["month"].max()
    aum_amc = aum_df[aum_df["month"] == latest]
    assert len(aum_amc) > 0

# PAGE 2
def p2_scatter():
    latest_yr = perf_df["date"].dt.year.max() if "date" in perf_df.columns else 2026
    pp = (perf_df.merge(funds[["fund_id","scheme_name","category"]], on="fund_id")
          .merge(aum_df[aum_df["month"] == aum_df["month"].max()][["amc","aum_cr"]],
                 on="amc", how="left"))
    assert len(pp) > 0, f"Expected >0, got {len(pp)}"

def p2_scorecard():
    scorecard2 = scorecard.rename(columns={"amfi_code": "fund_id"}) if "amfi_code" in scorecard.columns else scorecard
    sc = scorecard2.merge(funds[["fund_id","amc"]], on="fund_id", how="left")
    assert "overall_rank" in sc.columns

def p2_nav_bm():
    fid = funds["fund_id"].iloc[0]
    fn  = nav_df[nav_df["fund_id"] == fid].sort_values("date")
    fn["idx"] = fn["nav"] / fn["nav"].iloc[0] * 100
    bm50 = bm_df[bm_df["index_name"] == "NIFTY50"].sort_values("date")
    bm50["idx"] = bm50["close_value"] / bm50["close_value"].iloc[0] * 100
    assert len(fn) > 0 and len(bm50) > 0

# PAGE 3
def p3_city():
    city = (txn_df.groupby("city")["amount"].sum() / 1e7).nlargest(15)
    assert len(city) > 0

def p3_txn_split():
    split = txn_df.groupby("txn_type")["amount"].sum()
    assert len(split) > 0

def p3_age_sip():
    txn_copy = txn_df.copy()
    sip_age = txn_copy[txn_copy["txn_type"].str.upper() == "SIP"].groupby("age_group")["amount"].mean()
    assert len(sip_age) > 0

def p3_monthly_vol():
    txn_copy = txn_df.copy()
    txn_copy["month"] = txn_copy["txn_date"].dt.to_period("M").astype(str)
    vol = txn_copy.groupby("month")["amount"].sum() / 1e7
    assert len(vol) > 0

# PAGE 4
def p4_sip_nifty():
    sip_monthly = (txn_df[txn_df["txn_type"].str.upper() == "SIP"]
                   .groupby("txn_month")["amount"].sum() / 1e7).reset_index()
    sip_monthly.columns = ["month", "sip_cr"]

    nifty_monthly = (bm_df[bm_df["index_name"] == "NIFTY50"]
                     .assign(month=lambda d: d["date"].dt.to_period("M").astype(str))
                     .groupby("month")["close_value"].last().reset_index())
    merged = sip_monthly.merge(nifty_monthly[["month","close_value"]], on="month", how="inner")
    assert len(merged) > 0, f"merged empty — sip months: {sip_monthly.month.tolist()[:3]}"

def p4_cat_hmap():
    tc = txn_df[txn_df["txn_type"].str.upper().isin(["SIP","LUMPSUM"])].merge(
        funds[["fund_id","category"]], on="fund_id")
    tc["quarter"] = tc["txn_date"].dt.to_period("Q").astype(str)
    pivot = tc.groupby(["category","quarter"])["amount"].sum().unstack(fill_value=0)
    assert pivot.shape[0] > 0

def p4_net_inflow():
    ni = cat_inflows.groupby("category")["net_inflow_crore"].sum()
    assert ni is not None and len(ni) > 0

def p4_rolling():
    sip_monthly = (txn_df[txn_df["txn_type"].str.upper() == "SIP"]
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
