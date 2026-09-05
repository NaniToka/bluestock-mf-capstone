import sys

for fname in ["scripts/generate_report.py", "scripts/generate_presentation.py"]:
    try:
        with open(fname, "r") as f:
            c = f.read()

        c = c.replace('aum_df["month"].max()', 'aum_df["date"].max()')
        
        with open(fname, "w") as f:
            f.write(c)
    except FileNotFoundError:
        pass
