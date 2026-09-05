"""
generate_mock_data.py
---------------------
Generates 10 realistic synthetic CSV files for the Bluestock MF Analytics project.
Output: data/raw/*.csv
Covers date range 2022-01-01 to 2026-09-05, with Dec-2025 SIP milestone,
T30/B30 city flags, expense ratios, AMFI codes, and KYC fields.
"""

import os
import random
import numpy as np
import pandas as pd
from pathlib import Path

# ── reproducibility ──────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

# ── master fund universe ──────────────────────────────────────────────────────
FUNDS = [
    {"fund_id": "F001", "scheme_name": "Bluestock Large Cap Fund",        "amfi_code": 119598, "category": "Equity",  "sub_category": "Large Cap",      "amc": "Bluestock AMC",   "benchmark": "Nifty 100"},
    {"fund_id": "F002", "scheme_name": "Bluestock Mid Cap Opportunities",  "amfi_code": 120503, "category": "Equity",  "sub_category": "Mid Cap",        "amc": "Bluestock AMC",   "benchmark": "Nifty Midcap 150"},
    {"fund_id": "F003", "scheme_name": "Bluestock Flexi Cap Fund",         "amfi_code": 118825, "category": "Equity",  "sub_category": "Flexi Cap",      "amc": "Bluestock AMC",   "benchmark": "Nifty 500"},
    {"fund_id": "F004", "scheme_name": "Bluestock Short Duration Debt",    "amfi_code": 119270, "category": "Debt",    "sub_category": "Short Duration", "amc": "Bluestock AMC",   "benchmark": "Crisil ST Bond"},
    {"fund_id": "F005", "scheme_name": "Bluestock Liquid Fund",            "amfi_code": 120465, "category": "Debt",    "sub_category": "Liquid",         "amc": "Bluestock AMC",   "benchmark": "Crisil Liquid"},
    {"fund_id": "F006", "scheme_name": "Bluestock Hybrid Aggressive",      "amfi_code": 119801, "category": "Hybrid",  "sub_category": "Aggressive Hybrid","amc": "Bluestock AMC", "benchmark": "Nifty 50 Hybrid"},
    {"fund_id": "F007", "scheme_name": "Horizon Bluechip Fund",            "amfi_code": 135781, "category": "Equity",  "sub_category": "Large Cap",      "amc": "Horizon MF",      "benchmark": "Nifty 100"},
    {"fund_id": "F008", "scheme_name": "Pinnacle Small Cap Fund",          "amfi_code": 148742, "category": "Equity",  "sub_category": "Small Cap",      "amc": "Pinnacle MF",     "benchmark": "Nifty Smallcap 250"},
    {"fund_id": "F009", "scheme_name": "Apex Balanced Advantage",          "amfi_code": 152341, "category": "Hybrid",  "sub_category": "Balanced Advantage","amc": "Apex MF",      "benchmark": "Nifty 50 Hybrid"},
    {"fund_id": "F010", "scheme_name": "Summit Gilt Fund",                  "amfi_code": 163209, "category": "Debt",    "sub_category": "Gilt",           "amc": "Summit MF",       "benchmark": "Crisil Gilt"},
]
funds_df = pd.DataFrame(FUNDS)

# ── helper: business-day date range ──────────────────────────────────────────
START = pd.Timestamp("2022-01-01")
END   = pd.Timestamp("2026-09-05")
bdays = pd.bdate_range(START, END)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. fund_master.csv
# ═══════════════════════════════════════════════════════════════════════════════
fund_master = funds_df.copy()
expense_map = {"Equity": (0.80, 1.80), "Debt": (0.25, 0.80), "Hybrid": (0.60, 1.60)}
fund_master["expense_ratio"] = fund_master["category"].apply(
    lambda c: round(random.uniform(*expense_map[c]), 2)
)
fund_master["launch_date"]  = pd.to_datetime(
    [random.choice(pd.date_range("2010-01-01", "2021-12-31")) for _ in range(len(fund_master))]
).strftime("%Y-%m-%d")
fund_master["fund_manager"] = [
    "Rajesh Kumar", "Priya Mehta", "Amit Shah", "Sunita Rao",
    "Vikram Nair",  "Deepa Iyer",  "Arjun Patel","Neha Gupta",
    "Rahul Verma",  "Meera Joshi"
]
fund_master["aum_cr"]        = [round(random.uniform(500, 25000), 2) for _ in range(len(fund_master))]
fund_master["exit_load_pct"] = [round(random.choice([0.0, 0.5, 1.0]), 2)] * len(fund_master)
fund_master["lock_in_days"]  = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
fund_master.to_csv(RAW / "fund_master.csv", index=False)
print(f"[1] fund_master.csv  → {len(fund_master)} rows")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. nav_history.csv  (~10 funds × ~1200 bdays = ~12,000 rows)
# ═══════════════════════════════════════════════════════════════════════════════
nav_rows = []
# drift/vol per category
params = {"Equity": (0.0004, 0.013), "Debt": (0.00025, 0.002), "Hybrid": (0.0003, 0.008)}
for f in FUNDS:
    drift, vol = params[f["category"]]
    nav = round(random.uniform(15, 120), 2)
    for d in bdays:
        shock = np.random.normal(drift, vol)
        nav   = round(max(nav * (1 + shock), 5.0), 4)
        # seed ~1% NaN for cleaning exercise
        nav_val = np.nan if random.random() < 0.01 else nav
        nav_rows.append({"fund_id": f["fund_id"], "date": d.strftime("%Y-%m-%d"),
                         "nav": nav_val, "nav_change_pct": round(shock * 100, 4)})
nav_df = pd.DataFrame(nav_rows)
nav_df.to_csv(RAW / "nav_history.csv", index=False)
print(f"[2] nav_history.csv  → {len(nav_df)} rows")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. aum_history.csv  (monthly AUM per fund 2022-2026)
# ═══════════════════════════════════════════════════════════════════════════════
months = pd.date_range("2022-01-31", "2026-08-31", freq="ME")
aum_rows = []
for f in FUNDS:
    aum = random.uniform(500, 20000)
    for m in months:
        aum = max(aum * random.uniform(0.97, 1.06), 100)
        aum_rows.append({"fund_id": f["fund_id"], "month": m.strftime("%Y-%m"),
                         "aum_cr": round(aum, 2), "net_inflow_cr": round(random.uniform(-200, 800), 2)})
aum_df = pd.DataFrame(aum_rows)
aum_df.to_csv(RAW / "aum_history.csv", index=False)
print(f"[3] aum_history.csv  → {len(aum_df)} rows")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. investor_transactions.csv  (~50,000 rows)
# ═══════════════════════════════════════════════════════════════════════════════
N_INVESTORS = 2000
N_TXN       = 50000

T30_CITIES = ["Mumbai","Delhi","Bengaluru","Chennai","Hyderabad","Kolkata","Pune","Ahmedabad","Jaipur","Surat"]
B30_CITIES = ["Patna","Varanasi","Lucknow","Bhopal","Nagpur","Indore","Coimbatore","Kochi","Mysuru","Agra",
              "Ranchi","Guwahati","Bhubaneswar","Vadodara","Amritsar","Visakhapatnam","Rajkot","Meerut","Nashik","Ludhiana"]

investor_ids = [f"INV{str(i).zfill(5)}" for i in range(1, N_INVESTORS + 1)]
investor_meta = {}
for inv in investor_ids:
    city = random.choice(T30_CITIES + B30_CITIES)
    investor_meta[inv] = {
        "city": city,
        "city_tier": "T30" if city in T30_CITIES else "B30",
        "age": random.randint(22, 65),
        "gender": random.choice(["M", "F"]),
        "risk_profile": random.choice(["Conservative", "Moderate", "Aggressive"]),
        "kyc_status": random.choices(["Verified", "Pending", "Rejected"], weights=[85, 10, 5])[0],
    }

txn_types = ["SIP", "Lumpsum", "STP", "Redemption", "Switch"]
txn_weights = [45, 25, 10, 15, 5]

all_dates = pd.date_range(START, END, freq="D")

txn_rows = []
for _ in range(N_TXN):
    inv    = random.choice(investor_ids)
    meta   = investor_meta[inv]
    fund   = random.choice(FUNDS)
    date   = random.choice(all_dates)
    ttype  = random.choices(txn_types, weights=txn_weights)[0]
    # SIP amounts
    if ttype == "SIP":
        amount = random.choice([500, 1000, 2000, 3000, 5000, 10000])
    elif ttype == "Lumpsum":
        amount = round(random.uniform(5000, 500000), 2)
    elif ttype == "Redemption":
        amount = round(random.uniform(1000, 200000), 2)
    else:
        amount = round(random.uniform(1000, 100000), 2)

    units = round(amount / random.uniform(10, 200), 4)
    txn_rows.append({
        "txn_id": f"TXN{str(_+1).zfill(7)}",
        "investor_id": inv,
        "fund_id": fund["fund_id"],
        "txn_date": date.strftime("%Y-%m-%d"),
        "txn_type": ttype,
        "amount": amount,
        "units": units,
        "nav_at_txn": round(amount / units, 4),
        "city": meta["city"],
        "city_tier": meta["city_tier"],
        "age": meta["age"],
        "gender": meta["gender"],
        "kyc_status": meta["kyc_status"],
        "risk_profile": meta["risk_profile"],
        # seed some nulls
        "folio_no": f"FOLIO{random.randint(100000,999999)}" if random.random() > 0.02 else np.nan,
    })

txn_df = pd.DataFrame(txn_rows)
txn_df.to_csv(RAW / "investor_transactions.csv", index=False)
print(f"[4] investor_transactions.csv  → {len(txn_df)} rows")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. sip_register.csv  (active SIP mandates)
# ═══════════════════════════════════════════════════════════════════════════════
sip_rows = []
sip_investors = random.sample(investor_ids, 800)
for i, inv in enumerate(sip_investors):
    fund = random.choice(FUNDS)
    start_dt = random.choice(pd.date_range("2022-01-01", "2025-06-01", freq="MS"))
    # Dec-2025 milestone: ~40% of SIPs cross 36 instalments by Dec 2025
    instalments = random.randint(1, 48)
    sip_rows.append({
        "sip_id": f"SIP{str(i+1).zfill(6)}",
        "investor_id": inv,
        "fund_id": fund["fund_id"],
        "sip_amount": random.choice([500, 1000, 2000, 3000, 5000, 10000]),
        "sip_date": random.randint(1, 28),
        "start_date": start_dt.strftime("%Y-%m-%d"),
        "frequency": random.choices(["Monthly", "Quarterly", "Weekly"], weights=[80, 15, 5])[0],
        "total_instalments_completed": instalments,
        "status": random.choices(["Active", "Paused", "Cancelled"], weights=[75, 15, 10])[0],
        "last_instalment_date": (start_dt + pd.DateOffset(months=instalments - 1)).strftime("%Y-%m-%d"),
        "mandate_amount": random.choice([500, 1000, 2000, 5000, 10000]),
    })
sip_df = pd.DataFrame(sip_rows)
sip_df.to_csv(RAW / "sip_register.csv", index=False)
print(f"[5] sip_register.csv  → {len(sip_df)} rows")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. scheme_performance.csv  (annual returns per fund)
# ═══════════════════════════════════════════════════════════════════════════════
perf_rows = []
for f in FUNDS:
    for yr in [2022, 2023, 2024, 2025]:
        if f["category"] == "Equity":
            ret_1y = round(random.uniform(-15, 45), 2)
        elif f["category"] == "Debt":
            ret_1y = round(random.uniform(4, 10), 2)
        else:
            ret_1y = round(random.uniform(-5, 28), 2)
        # some abnormal expense ratios seeded
        exp_ratio = round(random.uniform(0.2, 2.5), 2) if random.random() > 0.05 else round(random.uniform(3.5, 5.0), 2)
        perf_rows.append({
            "fund_id": f["fund_id"],
            "year": yr,
            "return_1y_pct": ret_1y,
            "return_3y_pct": round(ret_1y * 0.85 + random.uniform(-3, 3), 2),
            "return_5y_pct": round(ret_1y * 0.75 + random.uniform(-4, 4), 2),
            "benchmark_return_pct": round(ret_1y * 0.9 + random.uniform(-2, 2), 2),
            "alpha_pct": round(ret_1y - (ret_1y * 0.9 + random.uniform(-2, 2)), 2),
            "expense_ratio": exp_ratio,
            "sharpe_ratio": round(random.uniform(0.2, 2.5), 2),
            "std_dev": round(random.uniform(5, 25), 2),
            "category": f["category"],
        })
perf_df = pd.DataFrame(perf_rows)
perf_df.to_csv(RAW / "scheme_performance.csv", index=False)
print(f"[6] scheme_performance.csv  → {len(perf_df)} rows")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. portfolio_holdings.csv  (sector-level holdings per fund)
# ═══════════════════════════════════════════════════════════════════════════════
SECTORS = ["Financial Services", "IT", "FMCG", "Healthcare", "Energy",
           "Automobiles", "Metals", "Telecom", "Real Estate", "Infrastructure"]
months_q = pd.date_range("2022-03-31", "2026-06-30", freq="QE")
holding_rows = []
for f in FUNDS:
    if f["category"] == "Debt":
        continue  # equity/hybrid only
    for m in months_q:
        weights = np.random.dirichlet(np.ones(len(SECTORS))) * 100
        for sec, wt in zip(SECTORS, weights):
            holding_rows.append({
                "fund_id": f["fund_id"],
                "quarter_end": m.strftime("%Y-%m-%d"),
                "sector": sec,
                "allocation_pct": round(wt, 2),
                "num_stocks": random.randint(1, 12),
            })
holdings_df = pd.DataFrame(holding_rows)
holdings_df.to_csv(RAW / "portfolio_holdings.csv", index=False)
print(f"[7] portfolio_holdings.csv  → {len(holdings_df)} rows")

# ═══════════════════════════════════════════════════════════════════════════════
# 8. benchmark_returns.csv  (daily Nifty 100 / Nifty 50 / etc.)
# ═══════════════════════════════════════════════════════════════════════════════
benchmarks = ["Nifty 100", "Nifty Midcap 150", "Nifty 500",
              "Nifty Smallcap 250", "Nifty 50 Hybrid", "Crisil ST Bond",
              "Crisil Liquid", "Crisil Gilt"]
bm_rows = []
bm_levels = {b: random.uniform(5000, 20000) for b in benchmarks}
for d in bdays:
    for bm in benchmarks:
        drift = 0.0003 if "Nifty" in bm else 0.0002
        vol   = 0.010  if "Nifty" in bm else 0.001
        chg   = np.random.normal(drift, vol)
        bm_levels[bm] = max(bm_levels[bm] * (1 + chg), 100)
        bm_rows.append({
            "benchmark": bm,
            "date": d.strftime("%Y-%m-%d"),
            "index_value": round(bm_levels[bm], 2),
            "daily_return_pct": round(chg * 100, 4),
        })
bm_df = pd.DataFrame(bm_rows)
bm_df.to_csv(RAW / "benchmark_returns.csv", index=False)
print(f"[8] benchmark_returns.csv  → {len(bm_df)} rows")

# ═══════════════════════════════════════════════════════════════════════════════
# 9. investor_demographics.csv  (investor profile table)
# ═══════════════════════════════════════════════════════════════════════════════
demo_rows = []
for inv in investor_ids:
    meta = investor_meta[inv]
    demo_rows.append({
        "investor_id": inv,
        "age": meta["age"],
        "gender": meta["gender"],
        "city": meta["city"],
        "city_tier": meta["city_tier"],
        "risk_profile": meta["risk_profile"],
        "kyc_status": meta["kyc_status"],
        "annual_income_lakh": round(random.uniform(3, 100), 1),
        "occupation": random.choice(["Salaried", "Self-Employed", "Business", "Retired", "Student"]),
        "pan_verified": random.choices([True, False], weights=[90, 10])[0],
        "registration_date": random.choice(pd.date_range("2018-01-01", "2025-12-31")).strftime("%Y-%m-%d"),
    })
demo_df = pd.DataFrame(demo_rows)
demo_df.to_csv(RAW / "investor_demographics.csv", index=False)
print(f"[9] investor_demographics.csv  → {len(demo_df)} rows")

# ═══════════════════════════════════════════════════════════════════════════════
# 10. distributor_data.csv
# ═══════════════════════════════════════════════════════════════════════════════
DISTRIBUTORS = [f"DIST{str(i).zfill(3)}" for i in range(1, 51)]
dist_rows = []
for d in DISTRIBUTORS:
    dist_rows.append({
        "distributor_id": d,
        "distributor_name": f"Distributor {d}",
        "city": random.choice(T30_CITIES + B30_CITIES),
        "city_tier": "T30" if random.random() < 0.5 else "B30",
        "arn_code": f"ARN-{random.randint(10000, 99999)}",
        "total_aum_cr": round(random.uniform(10, 5000), 2),
        "num_clients": random.randint(10, 2000),
        "sip_book_cr": round(random.uniform(1, 500), 2),
        "active_since": random.choice(pd.date_range("2005-01-01", "2020-12-31")).strftime("%Y-%m-%d"),
        "commission_type": random.choice(["Trail", "Upfront", "Both"]),
    })
dist_df = pd.DataFrame(dist_rows)
dist_df.to_csv(RAW / "distributor_data.csv", index=False)
print(f"[10] distributor_data.csv  → {len(dist_df)} rows")

print("\n✅ All 10 CSVs generated in data/raw/")
