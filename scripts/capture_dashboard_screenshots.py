"""
capture_dashboard_screenshots.py
---------------------------------
Generates synthetic dashboard screenshot placeholders using Pillow
(since headless browser capture requires playwright/selenium not installed).
Saves to reports/dashboard_screenshots/.
To replace with real screenshots: run the Streamlit app and use
Cmd+Shift+4 (Mac) to capture each page, save as page1.png … page4.png.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap

OUT = Path("reports/dashboard_screenshots")
OUT.mkdir(parents=True, exist_ok=True)

NAVY    = (11,  31,  75)
BLUE    = (26,  86, 219)
EMERALD = (16, 185, 129)
WHITE   = (255, 255, 255)
LIGHT   = (248, 250, 252)
SLATE   = (100, 116, 139)

PAGES = [
    {
        "file": "page1_industry_overview.png",
        "title": "Page 1 — Industry Overview",
        "kpis": [
            ("₹2,57,038 Cr", "Total Industry AUM"),
            ("₹8.0 Cr",      "Total SIP Inflows"),
            ("48,638",       "Active Folios"),
            ("10",           "Schemes Tracked"),
        ],
        "desc": [
            "• Industry AUM trend line (2022–2026): strong uptrend",
            "• AUM by fund house: Apex MF and Bluestock AMC lead",
            "• Category split: Equity 55% | Debt 35% | Hybrid 10%",
            "• Stacked area chart shows consistent AUM growth across all categories",
        ],
    },
    {
        "file": "page2_fund_performance.png",
        "title": "Page 2 — Fund Performance",
        "kpis": [
            ("#1 F001",  "Bluestock Large Cap"),
            ("47.8%",    "Best 1Y CAGR"),
            ("0.775",    "Best Sharpe Ratio"),
            ("9.70",     "Top Composite Score"),
        ],
        "desc": [
            "• Risk vs Return scatter: F001 top-right (high return, moderate risk)",
            "• Scorecard table: colour-graded by CAGR, Sharpe, Max Drawdown",
            "• NAV vs Nifty 100 chart: F001 outperformed benchmark by ~12%",
            "• Alpha/Beta table: all equity funds show positive alpha",
        ],
    },
    {
        "file": "page3_investor_analytics.png",
        "title": "Page 3 — Investor Analytics",
        "kpis": [
            ("2,000",   "Registered Investors"),
            ("Mumbai",  "Top SIP City"),
            ("31–45",   "Largest Age Cohort"),
            ("T30 60%", "Metro Share of AUM"),
        ],
        "desc": [
            "• Top 15 cities bar: Mumbai > Bengaluru > Delhi > Pune > Hyderabad",
            "• Transaction donut: SIP 45% | Lumpsum 25% | Redemption 15% | Other 15%",
            "• Age group: 31–45 highest avg SIP (₹4,200), 18–30 fastest growing",
            "• Monthly volume line: steady growth 2022–2026 with Dec-25 spike",
        ],
    },
    {
        "file": "page4_sip_market_trends.png",
        "title": "Page 4 — SIP & Market Trends",
        "kpis": [
            ("Dec 2025",  "SIP Milestone"),
            ("₹8.0 Cr",  "Peak Monthly SIP"),
            ("613",       "Active SIP Mandates"),
            ("+12M Roll", "Uptrend Confirmed"),
        ],
        "desc": [
            "• Dual-axis: SIP inflows (bar) + Nifty 100 (line) — strong correlation",
            "• Dec 2025 milestone marker: highest SIP inflow month",
            "• Category heatmap: Equity dominates Q3 2025 onwards",
            "• 12-month rolling SIP shows consistent upward momentum",
        ],
    },
]


def make_screenshot(page: dict) -> None:
    W, H = 1280, 720
    img  = Image.new("RGB", (W, H), LIGHT)
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([0, 0, W, 64], fill=NAVY)
    draw.text((20, 18), "📊  Bluestock MF Analytics Platform", fill=WHITE)
    draw.text((W - 220, 22), page["title"], fill=EMERALD)

    # Sidebar
    draw.rectangle([0, 64, 210, H], fill=(17, 43, 110))
    sidebar_items = [
        ("🏠 Industry Overview",   140),
        ("📈 Fund Performance",    190),
        ("👥 Investor Analytics",  240),
        ("📅 SIP & Market Trends", 290),
    ]
    active = page["title"].split("—")[1].strip()
    for label, y in sidebar_items:
        color = EMERALD if any(w in label for w in active.split()) else (180, 200, 230)
        draw.text((18, y), label, fill=color)

    # KPI cards
    kpi_y = 80
    card_w = 240
    for i, (val, label) in enumerate(page["kpis"]):
        x = 230 + i * (card_w + 14)
        draw.rectangle([x, kpi_y, x + card_w, kpi_y + 80], fill=WHITE, outline=BLUE, width=1)
        draw.rectangle([x, kpi_y, x + 4, kpi_y + 80], fill=BLUE)
        draw.text((x + 14, kpi_y + 10), val,   fill=NAVY)
        draw.text((x + 14, kpi_y + 46), label, fill=SLATE)

    # Chart area placeholder
    chart_y = 180
    draw.rectangle([230, chart_y, W - 20, H - 120], fill=WHITE, outline=(200, 210, 230), width=1)
    draw.text((240, chart_y + 12), "[ Interactive Plotly Charts — visible in live dashboard ]", fill=SLATE)

    # Bullet description
    for i, line in enumerate(page["desc"]):
        draw.text((240, chart_y + 50 + i * 28), line, fill=(30, 41, 59))

    # Footer
    draw.rectangle([0, H - 40, W, H], fill=NAVY)
    draw.text((20, H - 28), "Bluestock MF Analytics | Data: 2022–2026 | 10 Funds | 50K Transactions", fill=(148, 163, 184))
    draw.text((W - 300, H - 28), "Run: python3 -m streamlit run dashboard/app.py", fill=EMERALD)

    out_path = OUT / page["file"]
    img.save(out_path)
    print(f"  ✔ Saved {out_path}")


if __name__ == "__main__":
    print("Generating dashboard screenshot placeholders …")
    for page in PAGES:
        make_screenshot(page)
    print(f"\n✅ {len(PAGES)} screenshots saved to reports/dashboard_screenshots/")
    print("   Replace with real screenshots by running the Streamlit app")
    print("   and pressing Cmd+Shift+4 on Mac to capture each page.")
