import sys

for fname in ["scripts/generate_report.py", "scripts/generate_presentation.py"]:
    try:
        with open(fname, "r") as f:
            c = f.read()

        c = c.replace('aum_df["date"].max()', 'aum_df["month"].max()')
        c = c.replace('aum_df  = pd.read_sql("SELECT * FROM fact_aum", conn)', 'aum_df  = pd.read_sql("SELECT * FROM fact_aum", conn)\n    aum_df = aum_df.rename(columns={"date": "month", "aum_crore": "aum_cr", "fund_house": "amc"})')
        c = c.replace('txn_df  = pd.read_sql("SELECT * FROM fact_transactions", conn)', 'txn_df  = pd.read_sql("SELECT * FROM fact_transactions", conn)\n    txn_df = txn_df.rename(columns={"transaction_date": "txn_date", "amfi_code": "fund_id", "transaction_type": "txn_type", "amount_inr": "amount"})')
        c = c.replace('fund_df = pd.read_sql("SELECT * FROM dim_fund", conn)', 'fund_df = pd.read_sql("SELECT * FROM dim_fund", conn)\n    fund_df = fund_df.rename(columns={"amfi_code": "fund_id", "fund_house": "amc"})')

        with open(fname, "w") as f:
            f.write(c)
    except FileNotFoundError:
        pass
