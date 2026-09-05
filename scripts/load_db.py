"""
load_db.py
----------
Creates the SQLite star-schema database at data/db/bluestock_mf.db,
loads all processed CSVs via SQLAlchemy, and verifies row counts.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

DB_PATH   = Path("data/db/bluestock_mf.db")
SCHEMA_SQL = Path("sql/schema.sql")
PROCESSED  = Path("data/processed")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Remove existing DB for clean load
if DB_PATH.exists():
    DB_PATH.unlink()
    print("  Removed existing DB for clean reload.")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def run_schema() -> None:
    """Execute schema.sql DDL against the SQLite database."""
    ddl = SCHEMA_SQL.read_text(encoding="utf-8")
    with engine.connect() as conn:
        # SQLite: run each statement separately
        for stmt in ddl.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()
    print("  ✔ Schema created from sql/schema.sql")


def load_table(df: pd.DataFrame, table: str, if_exists: str = "append") -> int:
    """Load DataFrame into SQLite table. Returns rows loaded."""
    df.to_sql(table, engine, if_exists=if_exists, index=False)
    return len(df)


def verify_counts() -> dict[str, int]:
    """Return row counts for every table."""
    tables = [
        "dim_fund", "dim_investor", "fact_nav", "fact_transactions",
        "fact_performance", "fact_aum", "fact_sip", "fact_holdings", "fact_benchmark"
    ]
    counts = {}
    with engine.connect() as conn:
        for t in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {t}"))
            counts[t] = result.scalar()
    return counts


if __name__ == "__main__":
    print("=" * 60)
    print("  Bluestock MF – Database Load")
    print("=" * 60)

    run_schema()

    # ── dim_fund ────────────────────────────────────────────────
    print("\n  Loading dim_fund …")
    fund_df = pd.read_csv(PROCESSED / "fund_master_clean.csv")
    n = load_table(fund_df, "dim_fund")
    print(f"    → {n} rows")

    # ── dim_investor ─────────────────────────────────────────────
    print("  Loading dim_investor …")
    inv_df = pd.read_csv(PROCESSED / "investor_demographics_clean.csv")
    inv_df["pan_verified"] = inv_df["pan_verified"].astype(int)
    n = load_table(inv_df, "dim_investor")
    print(f"    → {n} rows")

    # ── fact_nav ──────────────────────────────────────────────────
    print("  Loading fact_nav …")
    nav_df = pd.read_csv(PROCESSED / "nav_history_clean.csv")
    n = load_table(nav_df[["fund_id", "date", "nav", "nav_change_pct"]], "fact_nav")
    print(f"    → {n} rows")

    # ── fact_transactions ─────────────────────────────────────────
    print("  Loading fact_transactions …")
    txn_df = pd.read_csv(PROCESSED / "investor_transactions_clean.csv", parse_dates=["txn_date"])
    txn_df["txn_date"]  = txn_df["txn_date"].dt.strftime("%Y-%m-%d")
    txn_df["kyc_valid"] = txn_df["kyc_valid"].astype(int)
    keep_cols = ["txn_id","investor_id","fund_id","txn_date","txn_month","txn_type",
                 "amount","units","nav_at_txn","city","city_tier","kyc_status",
                 "kyc_valid","folio_no","risk_profile"]
    n = load_table(txn_df[keep_cols], "fact_transactions")
    print(f"    → {n} rows")

    # ── fact_performance ──────────────────────────────────────────
    print("  Loading fact_performance …")
    perf_df = pd.read_csv(PROCESSED / "scheme_performance_clean.csv")
    perf_df["expense_ratio_flagged"] = perf_df["expense_ratio_flagged"].astype(int)
    n = load_table(perf_df, "fact_performance")
    print(f"    → {n} rows")

    # ── fact_aum ──────────────────────────────────────────────────
    print("  Loading fact_aum …")
    aum_df = pd.read_csv(PROCESSED / "aum_history_clean.csv")
    n = load_table(aum_df, "fact_aum")
    print(f"    → {n} rows")

    # ── fact_sip ──────────────────────────────────────────────────
    print("  Loading fact_sip …")
    sip_df = pd.read_csv(PROCESSED / "sip_register_clean.csv")
    n = load_table(sip_df, "fact_sip")
    print(f"    → {n} rows")

    # ── fact_holdings ─────────────────────────────────────────────
    print("  Loading fact_holdings …")
    hold_df = pd.read_csv(PROCESSED / "portfolio_holdings_clean.csv")
    n = load_table(hold_df, "fact_holdings")
    print(f"    → {n} rows")

    # ── fact_benchmark ────────────────────────────────────────────
    print("  Loading fact_benchmark …")
    bm_df = pd.read_csv(PROCESSED / "benchmark_returns_clean.csv")
    n = load_table(bm_df, "fact_benchmark")
    print(f"    → {n} rows")

    # ── Verify ────────────────────────────────────────────────────
    print("\n--- Row Count Verification ---")
    counts = verify_counts()
    for table, cnt in counts.items():
        print(f"  {table:30s} {cnt:>7,}")

    # assertions
    assert counts["dim_fund"]          == 10,    f"dim_fund: expected 10, got {counts['dim_fund']}"
    assert counts["dim_investor"]      == 2000,  f"dim_investor: expected 2000"
    assert counts["fact_nav"]          == 12200, f"fact_nav: expected 12200"
    assert counts["fact_transactions"] == 50000, f"fact_transactions: expected 50000"
    assert counts["fact_aum"]          == 560,   f"fact_aum: expected 560"
    assert counts["fact_benchmark"]    == 9760,  f"fact_benchmark: expected 9760"

    print(f"\n✅ Database ready at {DB_PATH}")
    print("✅ All row-count assertions passed.")
