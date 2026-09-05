"""
load_db.py
----------
Rebuilds data/db/bluestock_mf.db from real cleaned CSVs.
Primary join key: amfi_code.
"""

import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

DB_PATH    = Path("data/db/bluestock_mf.db")
SCHEMA_SQL = Path("sql/schema.sql")
PROCESSED  = Path("data/processed")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

if DB_PATH.exists():
    DB_PATH.unlink()
    print("  Removed old DB.")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def run_schema():
    ddl = SCHEMA_SQL.read_text(encoding="utf-8")
    with engine.connect() as conn:
        for stmt in ddl.split(";"):
            s = stmt.strip()
            if s:
                conn.execute(text(s))
        conn.commit()
    print("  ✔ Schema created.")


def load(df, table):
    df.to_sql(table, engine, if_exists="append", index=False)
    return len(df)


def verify():
    tables = ["dim_fund","fact_nav","fact_aum","fact_sip_inflows",
              "fact_category_inflows","fact_folio_count","fact_performance",
              "fact_transactions","fact_holdings","fact_benchmark"]
    counts = {}
    with engine.connect() as conn:
        for t in tables:
            counts[t] = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
    return counts


if __name__ == "__main__":
    print("=" * 60)
    print("  Bluestock MF – DB Load (Real Dataset)")
    print("=" * 60)
    run_schema()

    print("\n  Loading dim_fund …")
    fm = pd.read_csv(PROCESSED / "fund_master_clean.csv")
    fm["expense_ratio_flagged"] = fm["expense_ratio_flagged"].astype(int)
    print(f"    → {load(fm, 'dim_fund')} rows")

    print("  Loading fact_nav …")
    nav = pd.read_csv(PROCESSED / "nav_history_clean.csv")
    nav["date"] = pd.to_datetime(nav["date"]).dt.strftime("%Y-%m-%d")
    print(f"    → {load(nav[['amfi_code','date','nav','nav_change_pct']], 'fact_nav')} rows")

    print("  Loading fact_aum …")
    aum = pd.read_csv(PROCESSED / "aum_by_fund_house_clean.csv")
    aum["date"] = pd.to_datetime(aum["date"]).dt.strftime("%Y-%m-%d")
    print(f"    → {load(aum, 'fact_aum')} rows")

    print("  Loading fact_sip_inflows …")
    sip = pd.read_csv(PROCESSED / "monthly_sip_inflows_clean.csv")
    print(f"    → {load(sip, 'fact_sip_inflows')} rows")

    print("  Loading fact_category_inflows …")
    cat = pd.read_csv(PROCESSED / "category_inflows_clean.csv")
    print(f"    → {load(cat, 'fact_category_inflows')} rows")

    print("  Loading fact_folio_count …")
    fc = pd.read_csv(PROCESSED / "industry_folio_count_clean.csv")
    print(f"    → {load(fc, 'fact_folio_count')} rows")

    print("  Loading fact_performance …")
    perf = pd.read_csv(PROCESSED / "scheme_performance_clean.csv")
    perf["expense_ratio_flagged"] = perf["expense_ratio_flagged"].astype(int)
    print(f"    → {load(perf, 'fact_performance')} rows")

    print("  Loading fact_transactions …")
    txn = pd.read_csv(PROCESSED / "investor_transactions_clean.csv",
                      parse_dates=["transaction_date"])
    txn["transaction_date"] = txn["transaction_date"].dt.strftime("%Y-%m-%d")
    txn["kyc_valid"] = txn["kyc_valid"].astype(int)
    print(f"    → {load(txn, 'fact_transactions')} rows")

    print("  Loading fact_holdings …")
    hold = pd.read_csv(PROCESSED / "portfolio_holdings_clean.csv",
                       parse_dates=["portfolio_date"])
    hold["portfolio_date"] = hold["portfolio_date"].dt.strftime("%Y-%m-%d")
    print(f"    → {load(hold, 'fact_holdings')} rows")

    print("  Loading fact_benchmark …")
    bm = pd.read_csv(PROCESSED / "benchmark_indices_clean.csv",
                     parse_dates=["date"])
    bm["date"] = bm["date"].dt.strftime("%Y-%m-%d")
    print(f"    → {load(bm[['date','index_name','close_value','daily_return_pct']], 'fact_benchmark')} rows")

    print("\n--- Row Count Verification ---")
    for t, n in verify().items():
        print(f"  {t:30s} {n:>7,}")

    assert verify()["dim_fund"]          == 40,    "dim_fund"
    assert verify()["fact_nav"]          == 46000, "fact_nav"
    assert verify()["fact_transactions"] == 32778, "fact_transactions"
    assert verify()["fact_performance"]  == 40,    "fact_performance"

    print(f"\n✅ DB ready at {DB_PATH}")
    print("✅ All row-count assertions passed.")
