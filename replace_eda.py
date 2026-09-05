with open("scripts/generate_eda_notebook.py", "r") as f:
    c = f.read()

c = c.replace("latest_yr = perf_df['year'].max()", "latest_yr = 2026")
c = c.replace("perf_latest = perf_df[perf_df.year == latest_yr].merge", "perf_latest = perf_df.merge")
c = c.replace("perf_bar = perf_df[perf_df.year == latest_yr].merge", "perf_bar = perf_df.merge")
c = c.replace("std_dev", "std_dev_ann_pct")
c = c.replace("return_1y_pct", "return_1yr_pct")
c = c.replace("benchmark_return", "benchmark_3yr_pct")
c = c.replace("sub['return_1yr_pct'], width, label='Fund Return'", "sub['return_3yr_pct'], width, label='Fund Return'")

with open("scripts/generate_eda_notebook.py", "w") as f:
    f.write(c)
