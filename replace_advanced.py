with open("scripts/generate_advanced_notebook.py", "r") as f:
    c = f.read()

c = c.replace('quarter_end', 'portfolio_date')
c = c.replace('allocation_pct', 'weight_pct')

with open("scripts/generate_advanced_notebook.py", "w") as f:
    f.write(c)
