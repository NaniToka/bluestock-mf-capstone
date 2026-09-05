for fname in ["scripts/generate_report.py", "scripts/generate_presentation.py"]:
    try:
        with open(fname, "r") as f:
            c = f.read()

        c = c.replace('txn_df["folio_no"]', 'txn_df["investor_id"]')

        with open(fname, "w") as f:
            f.write(c)
    except FileNotFoundError:
        pass
