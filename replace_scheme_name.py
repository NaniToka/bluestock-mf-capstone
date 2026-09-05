with open("scripts/generate_eda_notebook.py", "r") as f:
    c = f.read()

c = c.replace("perf_bar = perf_df.merge(fund_df[['fund_id','scheme_name']], on='fund_id')", "perf_bar = perf_df.copy()")
c = c.replace("perf_latest = perf_df.merge(fund_df[['fund_id','scheme_name']], on='fund_id')", "perf_latest = perf_df.copy()")

with open("scripts/generate_eda_notebook.py", "w") as f:
    f.write(c)

with open("scripts/generate_advanced_notebook.py", "r") as f:
    c = f.read()

c = c.replace("perf_latest = perf_df.merge(fund_df[['fund_id','scheme_name']], on='fund_id')", "perf_latest = perf_df.copy()")

with open("scripts/generate_advanced_notebook.py", "w") as f:
    f.write(c)
