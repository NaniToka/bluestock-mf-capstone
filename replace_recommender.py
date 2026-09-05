with open("scripts/generate_advanced_notebook.py", "r") as f:
    c = f.read()

c = c.replace(
    "['overall_rank','fund_id','scheme_name','category','cagr_1y_pct','sharpe','composite_score']",
    "['overall_rank','amfi_code','scheme_name','category','return_1yr_pct','sharpe_ratio','composite_score']"
)

with open("scripts/generate_advanced_notebook.py", "w") as f:
    f.write(c)
