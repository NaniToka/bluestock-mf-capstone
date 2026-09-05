"""
dashboard/app.py
----------------
Bluestock MF Analytics Platform — Interactive Streamlit Dashboard
4 pages: Industry Overview | Fund Performance | Investor Analytics | SIP & Market Trends
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bluestock MF Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
DB   = BASE / "data" / "db" / "bluestock_mf.db"
PROC = BASE / "data" / "processed"

# ── Color theme ───────────────────────────────────────────────────────────────
NAVY    = "#0B1F4B"
BLUE    = "#1A56DB"
EMERALD = "#10B981"
TEAL    = "#0EA5E9"
AMBER   = "#F59E0B"
ROSE    = "#F43F5E"
SLATE   = "#64748B"
BG      = "#F8FAFC"

PALETTE = [BLUE, EMERALD, AMBER, ROSE, TEAL, "#8B5CF6", "#EC4899", "#F97316", "#14B8A6", "#6366F1"]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#F8FAFC",
    font=dict(family="Inter, sans-serif", color="#1E293B"),
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    /* Main background */
    .stApp {{ background-color: {BG}; }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {NAVY} 0%, #112B6E 100%);
    }}
    [data-testid="stSidebar"] * {{ color: #E2E8F0 !important; }}
    [data-testid="stSidebar"] .stRadio label {{ font-size: 0.95rem; }}

    /* Page title */
    .main-title {{
        background: linear-gradient(90deg, {NAVY}, {BLUE});
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.2rem;
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.3px;
    }}
    .main-title span {{ color: {EMERALD}; }}

    /* KPI cards */
    .kpi-card {{
        background: white;
        border-left: 4px solid {BLUE};
        border-radius: 10px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 8px rgba(0,0,0,0.07);
    }}
    .kpi-value {{ font-size: 1.8rem; font-weight: 700; color: {NAVY}; }}
    .kpi-label {{ font-size: 0.82rem; color: {SLATE}; margin-top: 2px; }}
    .kpi-delta {{ font-size: 0.8rem; color: {EMERALD}; font-weight: 600; }}

    /* Section headers */
    .section-header {{
        font-size: 1.05rem;
        font-weight: 600;
        color: {NAVY};
        border-bottom: 2px solid {BLUE};
        padding-bottom: 4px;
        margin: 1.2rem 0 0.8rem;
    }}

    /* Hide default streamlit header */
    #MainMenu, footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)

# ── DB loader (cached) ────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load(query: str) -> pd.DataFrame:
    conn = sqlite3.connect(DB)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(PROC / name)

# ── Pre-load core tables ───────────────────────────────────────────────────────
funds       = load("SELECT * FROM dim_fund")
funds       = funds.rename(columns={"amfi_code": "fund_id", "fund_house": "amc"})
nav_df      = load("SELECT * FROM fact_nav")
nav_df      = nav_df.rename(columns={"amfi_code": "fund_id"})
txn_df      = load("SELECT * FROM fact_transactions")
txn_df      = txn_df.rename(columns={"transaction_date": "txn_date", "amfi_code": "fund_id", "transaction_type": "txn_type", "amount_inr": "amount"})
aum_df      = load("SELECT * FROM fact_aum")
aum_df      = aum_df.rename(columns={"date": "month", "aum_crore": "aum_cr", "fund_house": "amc"})
sip_df      = load("SELECT * FROM fact_sip_inflows")
perf_df     = load("SELECT * FROM fact_performance")
perf_df     = perf_df.rename(columns={"amfi_code": "fund_id", "fund_house": "amc"})
bm_df       = load("SELECT * FROM fact_benchmark")
hold_df     = load("SELECT * FROM fact_holdings")
hold_df     = hold_df.rename(columns={"amfi_code": "fund_id"})
scorecard   = load_csv("fund_scorecard.csv")
alpha_beta  = load_csv("alpha_beta.csv")

nav_df["date"]     = pd.to_datetime(nav_df["date"])
txn_df["txn_date"] = pd.to_datetime(txn_df["txn_date"])
bm_df["date"]      = pd.to_datetime(bm_df["date"])
aum_df["month"]    = pd.to_datetime(aum_df["month"])
aum_df["month_dt"] = aum_df["month"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding: 1rem 0 1.5rem;'>
        <div style='font-size:2rem;'>📊</div>
        <div style='font-size:1.1rem; font-weight:700; color:white;'>Bluestock MF</div>
        <div style='font-size:0.75rem; color:#94A3B8;'>Analytics Platform</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["🏠 Industry Overview", "📈 Fund Performance",
         "👥 Investor Analytics", "📅 SIP & Market Trends"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(f"<div style='font-size:0.72rem;color:#64748B;'>Data: 2022–2026 | 10 funds | 50K txns</div>",
                unsafe_allow_html=True)

# ── Global title ──────────────────────────────────────────────────────────────
st.markdown("""
<div class='main-title'>
    📊 Bluestock MF <span>Analytics Platform</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Industry Overview
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Industry Overview":

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    latest_month = aum_df["month"].max()
    total_aum    = aum_df[aum_df["month"] == latest_month]["aum_cr"].sum()
    sip_inflows  = txn_df[txn_df["txn_type"].str.upper() == "SIP"]["amount"].sum() / 1e7
    folio_count  = txn_df["folio_no"].nunique()
    scheme_count = funds["fund_id"].nunique()

    # prev month for delta
    prev_months  = sorted(aum_df["month"].unique())
    prev_aum     = (aum_df[aum_df["month"] == prev_months[-2]]["aum_cr"].sum()
                    if len(prev_months) >= 2 else total_aum)
    aum_delta    = ((total_aum - prev_aum) / prev_aum * 100) if prev_aum else 0

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label, delta_str, icon in [
        (c1, f"₹{total_aum:,.0f} Cr", "Total Industry AUM",
         f"▲ {aum_delta:.1f}% vs prev month", "💰"),
        (c2, f"₹{sip_inflows:,.1f} Cr", "Total SIP Inflows (all-time)",
         f"{txn_df[txn_df.txn_type.str.upper()=='SIP'].shape[0]:,} SIP transactions", "📥"),
        (c3, f"{folio_count:,}", "Active Folios",
         f"{txn_df['investor_id'].nunique():,} registered investors", "📁"),
        (c4, f"{scheme_count}", "Schemes Tracked",
         f"{funds['amc'].nunique()} fund houses", "🏦"),
    ]:
        col.markdown(f"""
        <div class='kpi-card'>
            <div style='font-size:1.4rem'>{icon}</div>
            <div class='kpi-value'>{val}</div>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-delta'>{delta_str}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Industry AUM Trend ────────────────────────────────────────────────────
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown("<div class='section-header'>Industry AUM Trend (Monthly)</div>",
                    unsafe_allow_html=True)
        industry_aum = aum_df.groupby("month_dt")["aum_cr"].sum().reset_index()
        industry_aum.columns = ["Date", "AUM (₹ Cr)"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=industry_aum["Date"], y=industry_aum["AUM (₹ Cr)"],
            mode="lines", fill="tozeroy",
            line=dict(color=BLUE, width=2.5),
            fillcolor=f"rgba(26,86,219,0.12)",
            name="Industry AUM",
            hovertemplate="<b>%{x|%b %Y}</b><br>AUM: ₹%{y:,.0f} Cr<extra></extra>",
        ))
        fig.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text="Total Industry AUM (₹ Cr)", font=dict(size=13, color=NAVY)),
            xaxis_title="", yaxis_title="₹ Crore",
            yaxis=dict(tickformat=",.0f"),
            height=340,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("<div class='section-header'>AUM by Fund House</div>",
                    unsafe_allow_html=True)
        aum_by_amc = (aum_df[aum_df["month"] == latest_month]
                      .merge(funds[["fund_id","amc"]], on="fund_id")
                      .groupby("amc")["aum_cr"].sum()
                      .reset_index()
                      .sort_values("aum_cr", ascending=True))

        fig2 = go.Figure(go.Bar(
            x=aum_by_amc["aum_cr"], y=aum_by_amc["amc"],
            orientation="h",
            marker=dict(color=PALETTE[:len(aum_by_amc)], line=dict(width=0)),
            hovertemplate="<b>%{y}</b><br>AUM: ₹%{x:,.0f} Cr<extra></extra>",
        ))
        fig2.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text=f"AUM by AMC — {latest_month}", font=dict(size=13, color=NAVY)),
            xaxis_title="₹ Crore", yaxis_title="",
            height=340,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Category mix donut ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>AUM by Fund Category</div>",
                unsafe_allow_html=True)
    cat_aum = (aum_df[aum_df["month"] == latest_month]
               .merge(funds[["fund_id","category"]], on="fund_id")
               .groupby("category")["aum_cr"].sum().reset_index())

    col1, col2 = st.columns([1, 2])
    with col1:
        fig3 = go.Figure(go.Pie(
            labels=cat_aum["category"], values=cat_aum["aum_cr"],
            hole=0.55,
            marker=dict(colors=[BLUE, EMERALD, AMBER]),
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} Cr (%{percent})<extra></extra>",
        ))
        fig3.update_layout(**PLOTLY_LAYOUT, height=280,
                           title=dict(text="Category Split", font=dict(size=13, color=NAVY)))
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        monthly_cat = (aum_df.merge(funds[["fund_id","category"]], on="fund_id")
                       .groupby(["month_dt","category"])["aum_cr"].sum().reset_index())
        fig4 = px.area(monthly_cat, x="month_dt", y="aum_cr", color="category",
                       color_discrete_sequence=[BLUE, EMERALD, AMBER],
                       labels={"month_dt":"","aum_cr":"AUM (₹ Cr)","category":"Category"})
        fig4.update_layout(**PLOTLY_LAYOUT, height=280,
                           title=dict(text="Category AUM Over Time", font=dict(size=13, color=NAVY)))
        st.plotly_chart(fig4, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Fund Performance
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Fund Performance":

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Filters")
        sel_amc = st.multiselect("Fund House", funds["amc"].unique(),
                                 default=list(funds["amc"].unique()))
        sel_cat = st.multiselect("Category", funds["category"].unique(),
                                 default=list(funds["category"].unique()))

    filt_funds = funds[funds["amc"].isin(sel_amc) & funds["category"].isin(sel_cat)]
    filt_ids   = filt_funds["fund_id"].tolist()

    # ── Risk vs Return scatter ────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Risk vs Return (Latest Year)</div>",
                unsafe_allow_html=True)
    latest_yr  = perf_df["year"].max()
    # perf_df already has 'category' — only bring scheme_name and amc from funds
    perf_plot  = (perf_df[perf_df["year"] == latest_yr]
                  .merge(funds[["fund_id","scheme_name","amc"]], on="fund_id")
                  .merge(aum_df[aum_df["month"] == aum_df["month"].max()][["amc","aum_cr"]],
                       on="amc", how="left"))
    perf_plot  = perf_plot[perf_plot["fund_id"].isin(filt_ids)]

    fig = px.scatter(
        perf_plot, x="std_dev", y="return_1y_pct",
        size="aum_cr", color="category", text="fund_id",
        color_discrete_sequence=[BLUE, EMERALD, AMBER],
        labels={"std_dev":"Std Dev (Risk %)", "return_1y_pct":"1Y Return (%)",
                "aum_cr":"AUM (₹ Cr)", "category":"Category"},
        hover_data={"scheme_name":True,"aum_cr":":.0f","std_dev":":.1f",
                    "return_1y_pct":":.1f","fund_id":False},
        size_max=55,
    )
    fig.update_traces(textposition="top center", textfont=dict(size=9))
    fig.add_hline(y=0, line_dash="dash", line_color=SLATE, line_width=1)
    fig.update_layout(
        **PLOTLY_LAYOUT, height=400,
        title=dict(text=f"Risk vs Return — {latest_yr}  (bubble size = AUM)",
                   font=dict(size=13, color=NAVY)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Scorecard table ───────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Fund Scorecard</div>", unsafe_allow_html=True)
    sc_display = (scorecard.merge(funds[["fund_id","amc"]], on="fund_id", how="left")
                  [scorecard["fund_id"].isin(filt_ids)])
    sc_cols = ["overall_rank","fund_id","scheme_name","category",
               "cagr_1y_pct","cagr_3y_pct","sharpe","sortino",
               "max_drawdown_pct","composite_score"]
    sc_show = sc_display[sc_cols].rename(columns={
        "overall_rank":"Rank","fund_id":"Fund ID","scheme_name":"Scheme",
        "category":"Category","cagr_1y_pct":"CAGR 1Y%","cagr_3y_pct":"CAGR 3Y%",
        "sharpe":"Sharpe","sortino":"Sortino",
        "max_drawdown_pct":"Max DD%","composite_score":"Score",
    }).sort_values("Rank")

    st.dataframe(
        sc_show.style
            .background_gradient(subset=["CAGR 1Y%","Sharpe","Score"], cmap="Blues")
            .background_gradient(subset=["Max DD%"], cmap="Reds_r")
            .format({"CAGR 1Y%":"{:.1f}","CAGR 3Y%":"{:.1f}",
                     "Sharpe":"{:.2f}","Sortino":"{:.2f}",
                     "Max DD%":"{:.1f}","Score":"{:.2f}"}),
        use_container_width=True,
        height=360,
    )

    # ── NAV vs Benchmark ──────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>NAV vs Benchmark Comparison</div>",
                unsafe_allow_html=True)

    col_sel, _ = st.columns([1, 2])
    with col_sel:
        sel_fund = st.selectbox(
            "Select Fund",
            filt_ids,
            format_func=lambda x: funds.loc[funds.fund_id==x, "scheme_name"].values[0],
        )

    fund_nav = nav_df[nav_df["fund_id"] == sel_fund][["date","nav"]].copy()
    fund_nav = fund_nav.sort_values("date")
    # normalise to 100 at start
    fund_nav["idx"] = fund_nav["nav"] / fund_nav["nav"].iloc[0] * 100

    bm_nifty50  = bm_df[bm_df["index_name"] == "NIFTY100"][["date","index_value"]].copy()
    bm_nifty50  = bm_nifty50.sort_values("date")
    bm_nifty50["idx"] = bm_nifty50["close_value"] / bm_nifty50["close_value"].iloc[0] * 100

    bm_nifty100 = bm_df[bm_df["index_name"] == "NIFTY500"][["date","index_value"]].copy()
    bm_nifty100 = bm_nifty100.sort_values("date")
    bm_nifty100["idx"] = bm_nifty100["close_value"] / bm_nifty100["close_value"].iloc[0] * 100

    fname = funds.loc[funds.fund_id == sel_fund, "scheme_name"].values[0]
    fig_nav = go.Figure()
    fig_nav.add_trace(go.Scatter(
        x=fund_nav["date"], y=fund_nav["idx"],
        name=fname[:30], line=dict(color=BLUE, width=2.2),
        hovertemplate="%{x|%d %b %Y}<br>Value: %{y:.1f}<extra></extra>",
    ))
    fig_nav.add_trace(go.Scatter(
        x=bm_nifty50["date"], y=bm_nifty50["idx"],
        name="Nifty 100", line=dict(color=EMERALD, width=1.8, dash="dot"),
        hovertemplate="%{x|%d %b %Y}<br>Nifty 100: %{y:.1f}<extra></extra>",
    ))
    fig_nav.add_trace(go.Scatter(
        x=bm_nifty100["date"], y=bm_nifty100["idx"],
        name="Nifty 500", line=dict(color=AMBER, width=1.8, dash="dash"),
        hovertemplate="%{x|%d %b %Y}<br>Nifty 500: %{y:.1f}<extra></extra>",
    ))
    fig_nav.update_layout(
        **PLOTLY_LAYOUT, height=380,
        title=dict(text=f"Indexed Performance: {fname[:35]} vs Benchmarks (Base=100)",
                   font=dict(size=13, color=NAVY)),
        yaxis_title="Indexed Value (Base=100)", xaxis_title="",
    )
    st.plotly_chart(fig_nav, use_container_width=True)

    # ── Alpha / Beta table ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Alpha & Beta (vs Nifty 100)</div>",
                unsafe_allow_html=True)
    ab_show = (alpha_beta[alpha_beta["fund_id"].isin(filt_ids)]
               .rename(columns={"fund_id":"Fund ID","scheme_name":"Scheme",
                                 "category":"Category","alpha_ann":"Alpha (ann.)",
                                 "beta":"Beta","r_squared":"R²"}))
    st.dataframe(
        ab_show.style.format({"Alpha (ann.)":"{:.4f}","Beta":"{:.3f}","R²":"{:.3f}"}),
        use_container_width=True, height=280,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Investor Analytics
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Investor Analytics":

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Filters")
        all_tiers  = txn_df["city_tier"].dropna().unique().tolist()
        sel_tier   = st.multiselect("City Tier", all_tiers, default=all_tiers)

        all_cities = sorted(txn_df["city"].dropna().unique().tolist())
        sel_cities = st.multiselect("City (top picks)", all_cities,
                                    default=all_cities[:10])

        age_groups = ["18-25", "26-35", "36-45", "46-55", "56+"]
        sel_age    = st.multiselect("Age Group", age_groups, default=age_groups)

    txn_aug = txn_df.copy()
    txn_aug["age_band"] = txn_aug["age_group"]
    txn_filt = txn_aug[
        txn_aug["city_tier"].isin(sel_tier) &
        txn_aug["city"].isin(sel_cities) &
        txn_aug["age_group"].isin(sel_age)
    ]

    # ── Row 1 ─────────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("<div class='section-header'>Investment by City</div>",
                    unsafe_allow_html=True)
        city_agg = (txn_filt.groupby("city")["amount"].sum() / 1e7).nlargest(15).reset_index()
        city_agg.columns = ["City", "Amount (₹ Cr)"]
        fig = px.bar(city_agg.sort_values("Amount (₹ Cr)"), x="Amount (₹ Cr)", y="City",
                     orientation="h", color="Amount (₹ Cr)",
                     color_continuous_scale=[[0,TEAL],[1,NAVY]],
                     labels={"Amount (₹ Cr)":"₹ Cr"})
        fig.update_coloraxes(showscale=False)
        fig.update_layout(**PLOTLY_LAYOUT, height=400,
                          title=dict(text="Top Cities by Investment (₹ Cr)",
                                     font=dict(size=13, color=NAVY)))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("<div class='section-header'>Transaction Type Split</div>",
                    unsafe_allow_html=True)
        txn_split = txn_filt.groupby("txn_type")["amount"].sum().reset_index()
        txn_split.columns = ["Type", "Amount"]
        fig2 = go.Figure(go.Pie(
            labels=txn_split["Type"], values=txn_split["Amount"],
            hole=0.55,
            marker=dict(colors=PALETTE[:len(txn_split)]),
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} (%{percent})<extra></extra>",
        ))
        fig2.update_layout(
            **PLOTLY_LAYOUT, height=400,
            title=dict(text="SIP / Lumpsum / Redemption / Other Split",
                       font=dict(size=13, color=NAVY)),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2 ─────────────────────────────────────────────────────────────────
    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.markdown("<div class='section-header'>Age Group vs Avg SIP Amount</div>",
                    unsafe_allow_html=True)
        sip_age = (txn_filt[txn_filt["txn_type"] == "Sip"]
                   .groupby("age_band")["amount"].mean().reset_index())
        sip_age.columns = ["Age Group", "Avg SIP (₹)"]
        sip_age = sip_age.set_index("Age Group").loc[
            [g for g in age_groups if g in sip_age["Age Group"].values]
        ].reset_index()

        fig3 = px.bar(sip_age, x="Age Group", y="Avg SIP (₹)",
                      color="Age Group",
                      color_discrete_sequence=PALETTE[:len(age_groups)],
                      text="Avg SIP (₹)")
        fig3.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig3.update_layout(**PLOTLY_LAYOUT, height=360, showlegend=False,
                           title=dict(text="Average SIP Amount by Age Group",
                                      font=dict(size=13, color=NAVY)))
        st.plotly_chart(fig3, use_container_width=True)

    with col_r2:
        st.markdown("<div class='section-header'>Monthly Transaction Volume</div>",
                    unsafe_allow_html=True)
        txn_filt_copy = txn_filt.copy()
        txn_filt_copy["month"] = txn_filt_copy["txn_date"].dt.to_period("M").astype(str)
        monthly_vol = (txn_filt_copy.groupby("month")["amount"].sum() / 1e7).reset_index()
        monthly_vol.columns = ["Month", "Volume (₹ Cr)"]
        monthly_vol["month_dt"] = pd.to_datetime(monthly_vol["Month"] + "-01")
        monthly_vol = monthly_vol.sort_values("month_dt")

        fig4 = go.Figure(go.Scatter(
            x=monthly_vol["month_dt"], y=monthly_vol["Volume (₹ Cr)"],
            mode="lines+markers", line=dict(color=EMERALD, width=2),
            marker=dict(size=4),
            hovertemplate="%{x|%b %Y}<br>₹%{y:.1f} Cr<extra></extra>",
        ))
        fig4.update_layout(**PLOTLY_LAYOUT, height=360,
                           title=dict(text="Monthly Transaction Volume (₹ Cr)",
                                      font=dict(size=13, color=NAVY)),
                           xaxis_title="", yaxis_title="₹ Crore")
        st.plotly_chart(fig4, use_container_width=True)

    # ── T30 vs B30 ────────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>T30 vs B30 Investment Comparison</div>",
                unsafe_allow_html=True)
    tier_split = (txn_filt.groupby(["city_tier","txn_type"])["amount"].sum() / 1e7).reset_index()
    tier_split.columns = ["City Tier", "Txn Type", "Amount (₹ Cr)"]
    fig5 = px.bar(tier_split, x="Txn Type", y="Amount (₹ Cr)", color="City Tier",
                  barmode="group",
                  color_discrete_sequence=[BLUE, EMERALD],
                  labels={"Amount (₹ Cr)":"₹ Cr"})
    fig5.update_layout(**PLOTLY_LAYOUT, height=320,
                       title=dict(text="T30 vs B30: Investment by Transaction Type",
                                  font=dict(size=13, color=NAVY)))
    st.plotly_chart(fig5, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — SIP & Market Trends
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📅 SIP & Market Trends":

    # ── Dual-axis: SIP inflows (bar) + Nifty 100 (line) ─────────────────────
    st.markdown("<div class='section-header'>SIP Inflows vs Nifty 100 Index</div>",
                unsafe_allow_html=True)

    sip_monthly = (txn_df[txn_df["txn_type"].str.upper() == "SIP"]
                   .groupby("txn_month")["amount"].sum() / 1e7).reset_index()
    sip_monthly.columns = ["month", "sip_cr"]
    sip_monthly["month_dt"] = pd.to_datetime(sip_monthly["month"] + "-01")
    sip_monthly = sip_monthly.sort_values("month_dt")

    nifty_monthly = (bm_df[bm_df["index_name"] == "NIFTY100"]
                     .assign(month=lambda d: d["date"].dt.to_period("M").astype(str))
                     .groupby("month")["close_value"].last().reset_index())
    nifty_monthly["month_dt"] = pd.to_datetime(nifty_monthly["month"] + "-01")
    nifty_monthly = nifty_monthly.sort_values("month_dt")

    merged = sip_monthly.merge(nifty_monthly[["month", "index_value"]], on="month", how="inner")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=merged["month_dt"], y=merged["sip_cr"],
        name="SIP Inflow (₹ Cr)",
        marker=dict(color=BLUE, opacity=0.85),
        hovertemplate="%{x|%b %Y}<br>SIP: ₹%{y:.1f} Cr<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=merged["month_dt"], y=merged["close_value"],
        name="Nifty 100 Index",
        line=dict(color=EMERALD, width=2.5),
        hovertemplate="%{x|%b %Y}<br>Nifty 100: %{y:,.0f}<extra></extra>",
    ), secondary_y=True)

    # Dec-2025 milestone — use numeric timestamp for datetime x-axis
    import pandas as _pd
    milestone_x = _pd.Timestamp("2025-12-01").timestamp() * 1000
    fig.add_vline(x=milestone_x, line_dash="dot", line_color=AMBER,
                  annotation_text="Dec '25 Milestone", annotation_font_color=AMBER,
                  annotation_position="top right")

    fig.update_layout(
        **PLOTLY_LAYOUT, height=420,
        title=dict(text="Monthly SIP Inflows vs Nifty 100 (2022–2026)",
                   font=dict(size=13, color=NAVY)),
    )
    fig.update_layout(legend=dict(x=0.01, y=0.99))
    fig.update_yaxes(title_text="SIP Inflow (₹ Cr)", secondary_y=False)
    fig.update_yaxes(title_text="Nifty 100 Index", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    # ── Category inflow heatmap ────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Category Inflow Heatmap (Quarterly)</div>",
                unsafe_allow_html=True)

    txn_cat = (txn_df[txn_df["txn_type"].str.upper().isin(["SIP","LUMPSUM"])]
               .merge(funds[["fund_id","category"]], on="fund_id"))
    txn_cat["quarter"] = txn_cat["txn_date"].dt.to_period("Q").astype(str)
    cat_hmap = (txn_cat.groupby(["category","quarter"])["amount"].sum() / 1e7).reset_index()
    cat_hmap.columns = ["Category", "Quarter", "Inflow (₹ Cr)"]
    cat_pivot = cat_hmap.pivot(index="Category", columns="Quarter", values="Inflow (₹ Cr)").fillna(0)

    fig2 = go.Figure(go.Heatmap(
        z=cat_pivot.values,
        x=cat_pivot.columns.tolist(),
        y=cat_pivot.index.tolist(),
        colorscale=[[0,"#EFF6FF"],[0.5,TEAL],[1,NAVY]],
        hoverongaps=False,
        hovertemplate="<b>%{y}</b> | %{x}<br>₹%{z:.1f} Cr<extra></extra>",
        text=[[f"₹{v:.0f}" for v in row] for row in cat_pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=9),
    ))
    fig2.update_layout(
        **PLOTLY_LAYOUT, height=260,
        title=dict(text="Quarterly Category Inflows (₹ Cr)", font=dict(size=13, color=NAVY)),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Row: Top categories + SIP continuity ─────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("<div class='section-header'>Top 5 Categories by Net Inflow</div>",
                    unsafe_allow_html=True)
        ni = load("SELECT * FROM fact_category_inflows").groupby("category")["net_inflow_crore"].sum().reset_index()
        net_inflow = ni.sort_values("net_inflow_crore", ascending=False).head(5)
        net_inflow.columns = ["Category", "Net Inflow (₹ Cr)"]

        fig3 = px.bar(net_inflow, x="Category", y="Net Inflow (₹ Cr)",
                      color="Net Inflow (₹ Cr)",
                      color_continuous_scale=[[0, TEAL],[1, NAVY]],
                      text="Net Inflow (₹ Cr)")
        fig3.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig3.update_coloraxes(showscale=False)
        fig3.update_layout(**PLOTLY_LAYOUT, height=360, showlegend=False,
                           title=dict(text="Top Categories — Net Inflow (₹ Cr)",
                                      font=dict(size=13, color=NAVY)))
        st.plotly_chart(fig3, use_container_width=True)

    with col_r:
        st.markdown("<div class='section-header'>SIP Book Growth (Active SIPs)</div>",
                    unsafe_allow_html=True)
        sip_df_copy = sip_df.copy()
        sip_df_copy["month_dt"] = pd.to_datetime(sip_df_copy["month"] + "-01")
        sip_df_copy = sip_df_copy.sort_values("month_dt")

        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=sip_df_copy["month_dt"], y=sip_df_copy["active_sip_accounts_crore"],
            name="Active SIP Accts (Cr)", marker=dict(color=BLUE, opacity=0.8),
            hovertemplate="%{x|%b %Y}<br>%{y:.2f} Cr Accounts<extra></extra>",
        ))
        fig4.add_trace(go.Scatter(
            x=sip_df_copy["month_dt"], y=sip_df_copy["sip_aum_lakh_crore"],
            name="SIP AUM (Lakh Cr)", yaxis="y2",
            line=dict(color=EMERALD, width=2),
            hovertemplate="%{x|%b %Y}<br>₹%{y:.2f} Lakh Cr<extra></extra>",
        ))
        fig4.update_layout(
            **PLOTLY_LAYOUT, height=360,
            title=dict(text="Active SIP Accounts & AUM Growth", font=dict(size=13, color=NAVY)),
            yaxis=dict(title="Accounts (Crore)"),
            yaxis2=dict(title="SIP AUM (Lakh Crore)", overlaying="y", side="right"),
        )
        fig4.update_layout(legend=dict(x=0.01, y=0.99))
        st.plotly_chart(fig4, use_container_width=True)

    # ── Rolling SIP momentum ──────────────────────────────────────────────────
    st.markdown("<div class='section-header'>12-Month Rolling SIP Momentum</div>",
                unsafe_allow_html=True)
    sip_roll = sip_monthly.set_index("month_dt")["sip_cr"].rolling(12).sum().reset_index()
    sip_roll.columns = ["Date", "Rolling 12M SIP (₹ Cr)"]

    fig5 = go.Figure(go.Scatter(
        x=sip_roll["Date"], y=sip_roll["Rolling 12M SIP (₹ Cr)"],
        mode="lines", fill="tozeroy",
        line=dict(color=EMERALD, width=2.5),
        fillcolor="rgba(16,185,129,0.12)",
        hovertemplate="%{x|%b %Y}<br>12M SIP: ₹%{y:.1f} Cr<extra></extra>",
    ))
    fig5.update_layout(
        **PLOTLY_LAYOUT, height=300,
        title=dict(text="12-Month Rolling SIP Inflows (₹ Cr)",
                   font=dict(size=13, color=NAVY)),
        xaxis_title="", yaxis_title="₹ Crore",
    )
    st.plotly_chart(fig5, use_container_width=True)
