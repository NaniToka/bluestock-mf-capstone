for fname in ["scripts/generate_report.py", "scripts/generate_presentation.py"]:
    try:
        with open(fname, "r") as f:
            c = f.read()

        c = c.replace("return_1y_pct", "return_1yr_pct")
        c = c.replace("cagr_1y_pct", "return_1yr_pct")
        c = c.replace("['sharpe']", "['sharpe_ratio']")
        c = c.replace("{top_fund['sharpe']", "{top_fund['sharpe_ratio']")

        with open(fname, "w") as f:
            f.write(c)
    except FileNotFoundError:
        pass
