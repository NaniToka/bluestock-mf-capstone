"""
clean_data.py
-------------
Cleans the 10 real CSVs and saves to data/processed/.
Join key across all tables: amfi_code.
"""

import numpy as np
import pandas as pd
from pathlib import Path

RAW       = Path("data/raw")
PROCESSED = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)


def log(msg): print(f"  {msg}")
def save(df, name):
    df.to_csv(PROCESSED / name, index=False)
    log(f"✔ {name} → {df.shape}")


# ── 1. Fund Master ────────────────────────────────────────────────────────────
def clean_fund_master():
    print("\n[1] fund_master")
    df = pd.read_csv(RAW / "01_fund_master.csv")
    log(f"Raw: {df.shape}")
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")
    df["expense_ratio_pct"] = pd.to_numeric(df["expense_ratio_pct"], errors="coerce")
    # SEBI TER cap: equity 2.5%, debt 2.25%, hybrid 2.25%
    cap = {"Equity": 2.5, "Debt": 2.25, "Hybrid": 2.25}
    df["expense_ratio_flagged"] = df.apply(
        lambda r: r["expense_ratio_pct"] > cap.get(r["category"], 2.5), axis=1)
    df["expense_ratio_pct"] = df.apply(
        lambda r: min(r["expense_ratio_pct"], cap.get(r["category"], 2.5)), axis=1)
    save(df, "fund_master_clean.csv")
    return df


# ── 2. NAV History ────────────────────────────────────────────────────────────
def clean_nav_history():
    print("\n[2] nav_history")
    df = pd.read_csv(RAW / "02_nav_history.csv", parse_dates=["date"])
    log(f"Raw: {df.shape}  nulls={df.nav.isna().sum()}")
    df = df.sort_values(["amfi_code", "date"])
    df["nav"] = df.groupby("amfi_code")["nav"].transform(lambda s: s.ffill().bfill())
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    df = df[df["nav"] > 0]
    df["nav_change_pct"] = df.groupby("amfi_code")["nav"].pct_change().round(4) * 100
    save(df, "nav_history_clean.csv")
    return df


# ── 3. AUM by Fund House ──────────────────────────────────────────────────────
def clean_aum():
    print("\n[3] aum_by_fund_house")
    df = pd.read_csv(RAW / "03_aum_by_fund_house.csv", parse_dates=["date"])
    df = df.sort_values(["fund_house", "date"])
    save(df, "aum_by_fund_house_clean.csv")
    return df


# ── 4. Monthly SIP Inflows ───────────────────────────────────────────────────
def clean_sip_inflows():
    print("\n[4] monthly_sip_inflows")
    df = pd.read_csv(RAW / "04_monthly_sip_inflows.csv")
    # yoy_growth_pct is null for first year — expected
    df["yoy_growth_pct"] = df["yoy_growth_pct"].fillna(0)
    save(df, "monthly_sip_inflows_clean.csv")
    return df


# ── 5. Category Inflows ───────────────────────────────────────────────────────
def clean_category_inflows():
    print("\n[5] category_inflows")
    df = pd.read_csv(RAW / "05_category_inflows.csv")
    save(df, "category_inflows_clean.csv")
    return df


# ── 6. Industry Folio Count ───────────────────────────────────────────────────
def clean_folio_count():
    print("\n[6] industry_folio_count")
    df = pd.read_csv(RAW / "06_industry_folio_count.csv")
    save(df, "industry_folio_count_clean.csv")
    return df


# ── 7. Scheme Performance ─────────────────────────────────────────────────────
def clean_scheme_performance():
    print("\n[7] scheme_performance")
    df = pd.read_csv(RAW / "07_scheme_performance.csv")
    log(f"Raw: {df.shape}")
    for col in ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct"]:
        df[col] = df[col].clip(-100, 200)
    cap = {"Equity": 2.5, "Debt": 2.25, "Hybrid": 2.25, "Large Cap": 2.5,
           "Mid Cap": 2.5, "Small Cap": 2.5, "Flexi Cap": 2.5, "Gilt": 2.25}
    df["expense_ratio_flagged"] = df["expense_ratio_pct"] > 3.0
    df["expense_ratio_pct"] = df.apply(
        lambda r: min(r["expense_ratio_pct"], cap.get(r["category"], 2.5)), axis=1)
    save(df, "scheme_performance_clean.csv")
    return df


# ── 8. Investor Transactions ─────────────────────────────────────────────────
def clean_investor_transactions():
    print("\n[8] investor_transactions")
    df = pd.read_csv(RAW / "08_investor_transactions.csv",
                     parse_dates=["transaction_date"])
    log(f"Raw: {df.shape}")
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")
    df = df[df["amount_inr"] > 0]
    df["kyc_valid"] = df["kyc_status"] == "Verified"
    df["txn_month"] = df["transaction_date"].dt.to_period("M").astype(str)
    df["transaction_type"] = df["transaction_type"].str.strip().str.upper()
    save(df, "investor_transactions_clean.csv")
    return df


# ── 9. Portfolio Holdings ─────────────────────────────────────────────────────
def clean_portfolio_holdings():
    print("\n[9] portfolio_holdings")
    df = pd.read_csv(RAW / "09_portfolio_holdings.csv", parse_dates=["portfolio_date"])
    save(df, "portfolio_holdings_clean.csv")
    return df


# ── 10. Benchmark Indices ─────────────────────────────────────────────────────
def clean_benchmark_indices():
    print("\n[10] benchmark_indices")
    df = pd.read_csv(RAW / "10_benchmark_indices.csv", parse_dates=["date"])
    df = df.sort_values(["index_name", "date"])
    df["daily_return_pct"] = (df.groupby("index_name")["close_value"]
                                .pct_change().round(4) * 100)
    save(df, "benchmark_indices_clean.csv")
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("  Bluestock MF – Data Cleaning (Real Dataset)")
    print("=" * 60)

    clean_fund_master()
    clean_nav_history()
    clean_aum()
    clean_sip_inflows()
    clean_category_inflows()
    clean_folio_count()
    clean_scheme_performance()
    clean_investor_transactions()
    clean_portfolio_holdings()
    clean_benchmark_indices()

    files = list(PROCESSED.glob("*.csv"))
    assert len(files) >= 10, f"Only {len(files)} processed files"
    print(f"\n✅ {len(files)} cleaned files in {PROCESSED}")
    print("✅ All assertions passed.")
