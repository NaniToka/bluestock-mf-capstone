with open("dashboard/app.py", "r") as f:
    c = f.read()

c = c.replace('txn_df["txn_type"] == "Sip"', 'txn_df["txn_type"].str.upper() == "SIP"')
c = c.replace("txn_df.txn_type=='Sip'", "txn_df.txn_type.str.upper()=='SIP'")
c = c.replace('["txn_type"].isin(["Sip","Lumpsum"])', '["txn_type"].str.upper().isin(["SIP","LUMPSUM"])')
c = c.replace('bm_df["benchmark"] == "Nifty 100"', 'bm_df["index_name"] == "NIFTY100"')
c = c.replace('bm_df["benchmark"] == "Nifty 500"', 'bm_df["index_name"] == "NIFTY500"')
c = c.replace('bm_df["benchmark"] == "Nifty 50"', 'bm_df["index_name"] == "NIFTY50"')
c = c.replace('["index_value"]', '["close_value"]')
c = c.replace('.index_value', '.close_value')

with open("dashboard/app.py", "w") as f:
    f.write(c)
