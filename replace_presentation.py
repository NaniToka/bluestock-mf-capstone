with open("scripts/generate_presentation.py", "r") as f:
    c = f.read()

c = c.replace('txn_df["txn_type"] == "Sip"', 'txn_df["txn_type"].str.upper() == "SIP"')

with open("scripts/generate_presentation.py", "w") as f:
    f.write(c)
