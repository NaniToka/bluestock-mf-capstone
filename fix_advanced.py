with open("scripts/generate_advanced_notebook.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith("latest_yr = 2026"):
        skip = True
    if skip and line.strip() == "latest_q = hold_df['portfolio_date'].max()":
        skip = False
    
    if not skip:
        new_lines.append(line)

with open("scripts/generate_advanced_notebook.py", "w") as f:
    f.writelines(new_lines)
