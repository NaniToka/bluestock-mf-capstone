-- ============================================================
-- Bluestock MF Analytics – Star Schema DDL (SQLite)
-- Real dataset: amfi_code as primary join key
-- ============================================================

PRAGMA foreign_keys = ON;

-- Dimension: Funds
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code            INTEGER PRIMARY KEY,
    fund_house           TEXT,
    scheme_name          TEXT NOT NULL,
    category             TEXT,
    sub_category         TEXT,
    plan                 TEXT,
    launch_date          TEXT,
    benchmark            TEXT,
    expense_ratio_pct    REAL,
    expense_ratio_flagged INTEGER,
    exit_load_pct        REAL,
    min_sip_amount       REAL,
    min_lumpsum_amount   REAL,
    fund_manager         TEXT,
    risk_category        TEXT,
    sebi_category_code   TEXT
);

-- Fact: Daily NAV
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER REFERENCES dim_fund(amfi_code),
    date            TEXT NOT NULL,
    nav             REAL NOT NULL,
    nav_change_pct  REAL,
    UNIQUE(amfi_code, date)
);

-- Fact: AUM by Fund House (monthly)
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date                TEXT,
    fund_house          TEXT,
    aum_lakh_crore      REAL,
    aum_crore           REAL,
    num_schemes         INTEGER,
    UNIQUE(date, fund_house)
);

-- Fact: Monthly SIP Inflows (industry level)
CREATE TABLE IF NOT EXISTS fact_sip_inflows (
    sip_id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    month                      TEXT UNIQUE,
    sip_inflow_crore           REAL,
    active_sip_accounts_crore  REAL,
    new_sip_accounts_lakh      REAL,
    sip_aum_lakh_crore         REAL,
    yoy_growth_pct             REAL
);

-- Fact: Category Inflows (monthly)
CREATE TABLE IF NOT EXISTS fact_category_inflows (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    month           TEXT,
    category        TEXT,
    net_inflow_crore REAL,
    UNIQUE(month, category)
);

-- Fact: Industry Folio Count (monthly)
CREATE TABLE IF NOT EXISTS fact_folio_count (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    month                 TEXT UNIQUE,
    total_folios_crore    REAL,
    equity_folios_crore   REAL,
    debt_folios_crore     REAL,
    hybrid_folios_crore   REAL,
    others_folios_crore   REAL
);

-- Fact: Scheme Performance
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code               INTEGER REFERENCES dim_fund(amfi_code),
    scheme_name             TEXT,
    fund_house              TEXT,
    category                TEXT,
    plan                    TEXT,
    return_1yr_pct          REAL,
    return_3yr_pct          REAL,
    return_5yr_pct          REAL,
    benchmark_3yr_pct       REAL,
    alpha                   REAL,
    beta                    REAL,
    sharpe_ratio            REAL,
    sortino_ratio           REAL,
    std_dev_ann_pct         REAL,
    max_drawdown_pct        REAL,
    aum_crore               REAL,
    expense_ratio_pct       REAL,
    expense_ratio_flagged   INTEGER,
    morningstar_rating      INTEGER,
    risk_grade              TEXT
);

-- Fact: Investor Transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT,
    transaction_date    TEXT,
    txn_month           TEXT,
    amfi_code           INTEGER REFERENCES dim_fund(amfi_code),
    transaction_type    TEXT,
    amount_inr          REAL,
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT,
    kyc_valid           INTEGER
);

-- Fact: Portfolio Holdings (stock level)
CREATE TABLE IF NOT EXISTS fact_holdings (
    holding_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER REFERENCES dim_fund(amfi_code),
    stock_symbol    TEXT,
    stock_name      TEXT,
    sector          TEXT,
    weight_pct      REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date  TEXT
);

-- Fact: Benchmark Indices
CREATE TABLE IF NOT EXISTS fact_benchmark (
    bm_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date               TEXT,
    index_name         TEXT,
    close_value        REAL,
    daily_return_pct   REAL,
    UNIQUE(date, index_name)
);
