"""
live_nav_fetch.py
-----------------
Fetches current NAV data for 6 AMFI scheme codes via https://api.mfapi.in/mf/<code>.
Parses JSON, extracts latest NAV and recent history, saves to data/raw/live/.
Falls back to synthetic values if the API is unreachable (offline-safe).
"""

import json
import time
import requests
import pandas as pd
from pathlib import Path

LIVE_DIR = Path("data/raw/live")
LIVE_DIR.mkdir(parents=True, exist_ok=True)

# 6 AMFI codes from our fund universe
AMFI_CODES = [119598, 120503, 118825, 119270, 120465, 119801]
BASE_URL    = "https://api.mfapi.in/mf"
TIMEOUT     = 10  # seconds


def fetch_nav(amfi_code: int) -> dict | None:
    """Fetch NAV data from mfapi.in for one AMFI code. Returns parsed JSON or None."""
    url = f"{BASE_URL}/{amfi_code}"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  [WARN] Could not fetch {amfi_code}: {e}")
        return None


def synthetic_fallback(amfi_code: int) -> dict:
    """Generate a synthetic fallback payload matching mfapi.in structure."""
    import random, numpy as np
    random.seed(amfi_code)
    nav_val = round(random.uniform(20, 200), 4)
    data = []
    for i in range(30):
        d = pd.Timestamp("2026-09-05") - pd.Timedelta(days=i)
        nav_val = max(round(nav_val * (1 + random.uniform(-0.015, 0.015)), 4), 5.0)
        data.append({"date": d.strftime("%d-%m-%Y"), "nav": str(nav_val)})
    return {
        "meta": {
            "fund_house": "Bluestock AMC (Synthetic)",
            "scheme_type": "Open Ended Schemes",
            "scheme_category": "Equity",
            "scheme_code": amfi_code,
            "scheme_name": f"Synthetic Fund {amfi_code}",
        },
        "data": data,
        "status": "SYNTHETIC",
    }


def process_response(payload: dict, amfi_code: int) -> pd.DataFrame:
    """Convert mfapi.in JSON payload to a tidy DataFrame."""
    meta = payload.get("meta", {})
    rows = []
    for entry in payload.get("data", []):
        rows.append({
            "amfi_code":    amfi_code,
            "scheme_name":  meta.get("scheme_name", "Unknown"),
            "fund_house":   meta.get("fund_house", "Unknown"),
            "category":     meta.get("scheme_category", "Unknown"),
            "date":         entry["date"],
            "nav":          float(entry["nav"]),
            "source":       payload.get("status", "LIVE"),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("=" * 60)
    print("  Bluestock MF – Live NAV Fetch")
    print("=" * 60)

    all_dfs   = []
    summary   = []

    for code in AMFI_CODES:
        print(f"\n  Fetching AMFI {code} …", end=" ")
        payload = fetch_nav(code)
        status  = "LIVE"
        if payload is None:
            print("fallback → synthetic")
            payload = synthetic_fallback(code)
            status  = "SYNTHETIC"
        else:
            print(f"OK ({len(payload.get('data', []))} records)")

        df = process_response(payload, code)
        all_dfs.append(df)

        # save individual file
        out_path = LIVE_DIR / f"nav_live_{code}.csv"
        df.to_csv(out_path, index=False)

        latest_nav  = df["nav"].iloc[0] if not df.empty else "N/A"
        latest_date = df["date"].iloc[0] if not df.empty else "N/A"
        scheme_name = df["scheme_name"].iloc[0] if not df.empty else "N/A"
        summary.append({
            "amfi_code":   code,
            "scheme_name": scheme_name,
            "latest_date": latest_date,
            "latest_nav":  latest_nav,
            "records":     len(df),
            "source":      status,
        })
        time.sleep(0.3)  # polite rate-limit

    # combined file
    combined = pd.concat(all_dfs, ignore_index=True)
    combined_path = LIVE_DIR / "nav_live_combined.csv"
    combined.to_csv(combined_path, index=False)

    # print summary table
    print("\n--- Live NAV Summary ---")
    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False))

    print(f"\n✅ Live NAV data saved to {LIVE_DIR}/")
    print(f"   Combined file: {combined_path}  ({len(combined)} rows)")

    assert combined_path.exists(), "Combined live NAV file not created!"
    print("✅ Assertion passed.")
