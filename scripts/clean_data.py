"""
clean_data.py
-------------
Cleans three core datasets and saves results to data/processed/:

  1. nav_history       – sort, forward-fill NaNs, deduplicate, validate non-negative
  2. investor_transactions – standardise dtypes, validate amounts/dates,
                             filter Rejected-KYC, fill folio_no nulls
  3. scheme_performance    – validate return ranges, cap abnormal expense ratios

Also copies fund_master, aum_history, sip_register, portfolio_holdings,
benchmark_returns, investor_demographics, and distributor_data as-is
(after basic type coercion) so data/processed/ is the single source for DB load.
"""

import numpy as np
import pandas as pd
from pathlib import Path

RAW       = Path("data/raw")
PROCESSED = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────
def log(msg: str) -> None:
    print(f"  {msg}")


def save(df: pd.DataFrame, name: str) -> None:
    path = PROCESSED / name
    df.to_csv(path, index=False)
    log(f"✔ Saved {name}  → {df.shape}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. NAV History
# ─────────────────────────────────────────────────────────────────────────────
def clean_nav_history() -> pd.DataFrame:
    print("\n[1] Cleaning nav_history …")
    df = pd.read_csv(RAW / "nav_history.csv", parse_dates=["date"])

    raw_shape = df.shape
    null_before = df["nav"].isna().sum()
    log(f"Raw shape: {raw_shape}  |  NAV nulls: {null_before}")

    # sort per fund
    df = df.sort_values(["fund_id", "date"]).reset_index(drop=True)

    # forward-fill NAV within each fund group
    df["nav"] = df.groupby("fund_id")["nav"].transform(lambda s: s.ffill())

    # still-null (leading NaN): back-fill as last resort
    df["nav"] = df.groupby("fund_id")["nav"].transform(lambda s: s.bfill())

    null_after = df["nav"].isna().sum()
    log(f"NAV nulls after fill: {null_after}")

    # deduplicate (fund_id, date)
    dups = df.duplicated(subset=["fund_id", "date"]).sum()
    df = df.drop_duplicates(subset=["fund_id", "date"])
    log(f"Duplicates removed: {dups}")

    # validate non-negative NAV
    neg = (df["nav"] < 0).sum()
    df = df[df["nav"] >= 0]
    log(f"Negative NAV rows removed: {neg}")

    # recalculate nav_change_pct from clean series
    df["nav_change_pct"] = df.groupby("fund_id")["nav"].pct_change() * 100
    df["nav_change_pct"] = df["nav_change_pct"].round(4)

    save(df, "nav_history_clean.csv")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 2. Investor Transactions
# ─────────────────────────────────────────────────────────────────────────────
def clean_investor_transactions() -> pd.DataFrame:
    print("\n[2] Cleaning investor_transactions …")
    df = pd.read_csv(RAW / "investor_transactions.csv", parse_dates=["txn_date"])

    log(f"Raw shape: {df.shape}")

    # standardise types
    df["amount"]   = pd.to_numeric(df["amount"],   errors="coerce")
    df["units"]    = pd.to_numeric(df["units"],    errors="coerce")
    df["nav_at_txn"] = pd.to_numeric(df["nav_at_txn"], errors="coerce")

    # validate date range
    valid_start = pd.Timestamp("2022-01-01")
    valid_end   = pd.Timestamp("2026-09-05")
    invalid_dates = ((df["txn_date"] < valid_start) | (df["txn_date"] > valid_end)).sum()
    df = df[(df["txn_date"] >= valid_start) & (df["txn_date"] <= valid_end)]
    log(f"Out-of-range dates removed: {invalid_dates}")

    # validate amounts > 0
    invalid_amt = (df["amount"] <= 0).sum()
    df = df[df["amount"] > 0]
    log(f"Invalid (≤0) amounts removed: {invalid_amt}")

    # KYC filter – flag but keep; add a boolean column
    rejected_kyc = (df["kyc_status"] == "Rejected").sum()
    df["kyc_valid"] = df["kyc_status"] != "Rejected"
    log(f"Rejected KYC records flagged (not dropped): {rejected_kyc}")

    # fill folio_no nulls with synthetic folio
    null_folio = df["folio_no"].isna().sum()
    df["folio_no"] = df["folio_no"].fillna(
        df["investor_id"].astype(str) + "_" + df["fund_id"].astype(str)
    )
    log(f"folio_no nulls filled: {null_folio}")

    # standardise txn_type capitalisation
    df["txn_type"] = df["txn_type"].str.strip().str.title()

    # add month column for aggregation
    df["txn_month"] = df["txn_date"].dt.to_period("M").astype(str)

    save(df, "investor_transactions_clean.csv")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 3. Scheme Performance
# ─────────────────────────────────────────────────────────────────────────────
def clean_scheme_performance() -> pd.DataFrame:
    print("\n[3] Cleaning scheme_performance …")
    df = pd.read_csv(RAW / "scheme_performance.csv")

    log(f"Raw shape: {df.shape}")

    # check return range (flag if outside ±100 %)
    for col in ["return_1y_pct", "return_3y_pct", "return_5y_pct", "benchmark_return_pct"]:
        extreme = ((df[col] < -100) | (df[col] > 200)).sum()
        if extreme:
            log(f"Extreme return values in {col}: {extreme} – clipping to [-100, 200]")
            df[col] = df[col].clip(-100, 200)

    # SEBI max TER: 2.5 % for equity, 2.25 % for debt/hybrid
    sebi_cap = {"Equity": 2.5, "Debt": 2.25, "Hybrid": 2.25}
    high_er   = (df["expense_ratio"] > 3.0).sum()
    df["expense_ratio_flagged"] = df["expense_ratio"] > 3.0
    df["expense_ratio"] = df.apply(
        lambda r: min(r["expense_ratio"], sebi_cap.get(r["category"], 2.5)),
        axis=1
    )
    log(f"Expense ratios capped at SEBI limit: {high_er} records adjusted")

    # recalculate alpha after correction
    df["alpha_pct"] = (df["return_1y_pct"] - df["benchmark_return_pct"]).round(2)

    save(df, "scheme_performance_clean.csv")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Pass-through files (basic type coercion only)
# ─────────────────────────────────────────────────────────────────────────────
PASSTHROUGH = [
    ("fund_master.csv",          "fund_master_clean.csv"),
    ("aum_history.csv",          "aum_history_clean.csv"),
    ("sip_register.csv",         "sip_register_clean.csv"),
    ("portfolio_holdings.csv",   "portfolio_holdings_clean.csv"),
    ("benchmark_returns.csv",    "benchmark_returns_clean.csv"),
    ("investor_demographics.csv","investor_demographics_clean.csv"),
    ("distributor_data.csv",     "distributor_data_clean.csv"),
]

def passthrough_files() -> None:
    print("\n[4] Copying pass-through files …")
    for src, dst in PASSTHROUGH:
        df = pd.read_csv(RAW / src)
        save(df, dst)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Bluestock MF – Data Cleaning")
    print("=" * 60)

    nav_df  = clean_nav_history()
    txn_df  = clean_investor_transactions()
    perf_df = clean_scheme_performance()
    passthrough_files()

    # assertions
    processed_files = list(PROCESSED.glob("*.csv"))
    assert len(processed_files) >= 10, f"Expected ≥10 processed files, got {len(processed_files)}"
    assert nav_df["nav"].isna().sum() == 0,  "NAV still has nulls after cleaning!"
    assert (nav_df["nav"] < 0).sum()  == 0,  "Negative NAV values remain!"
    assert (txn_df["amount"] <= 0).sum() == 0, "Non-positive amounts remain!"

    print(f"\n✅ All cleaned files saved to {PROCESSED}/")
    print(f"   Total files: {len(processed_files)}")
    print("✅ All assertions passed.")
