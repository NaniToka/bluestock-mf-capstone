with open("scripts/generate_report.py", "r") as f:
    c = f.read()

c = c.replace('txn_df["txn_type"] == "Sip"', 'txn_df["txn_type"].str.upper() == "SIP"')
c = c.replace("txn_df.txn_type=='Sip'", "txn_df.txn_type.str.upper()=='SIP'")
c = c.replace('"fact_sip"', '"fact_sip_inflows"')

with open("scripts/generate_report.py", "w") as f:
    f.write(c)
