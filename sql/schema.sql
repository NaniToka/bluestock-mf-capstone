-- ============================================================
-- Bluestock MF Analytics – Star Schema DDL (SQLite)
-- ============================================================

PRAGMA foreign_keys = ON;

-- ────────────────────────────────────────────
-- Dimension: Funds
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_fund (
    fund_id          TEXT PRIMARY KEY,
    scheme_name      TEXT NOT NULL,
    amfi_code        INTEGER,
    category         TEXT,
    sub_category     TEXT,
    amc              TEXT,
    benchmark        TEXT,
    expense_ratio    REAL,
    launch_date      TEXT,
    fund_manager     TEXT,
    aum_cr           REAL,
    exit_load_pct    REAL,
    lock_in_days     INTEGER
);

-- ────────────────────────────────────────────
-- Dimension: Investors
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_investor (
    investor_id       TEXT PRIMARY KEY,
    age               INTEGER,
    gender            TEXT,
    city              TEXT,
    city_tier         TEXT,
    risk_profile      TEXT,
    kyc_status        TEXT,
    annual_income_lakh REAL,
    occupation        TEXT,
    pan_verified      INTEGER,   -- 0/1
    registration_date TEXT
);

-- ────────────────────────────────────────────
-- Fact: Daily NAV
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_id          TEXT    NOT NULL REFERENCES dim_fund(fund_id),
    date             TEXT    NOT NULL,
    nav              REAL    NOT NULL,
    nav_change_pct   REAL,
    UNIQUE(fund_id, date)
);

-- ────────────────────────────────────────────
-- Fact: Investor Transactions
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_id           TEXT PRIMARY KEY,
    investor_id      TEXT REFERENCES dim_investor(investor_id),
    fund_id          TEXT REFERENCES dim_fund(fund_id),
    txn_date         TEXT    NOT NULL,
    txn_month        TEXT,
    txn_type         TEXT,
    amount           REAL,
    units            REAL,
    nav_at_txn       REAL,
    city             TEXT,
    city_tier        TEXT,
    kyc_status       TEXT,
    kyc_valid        INTEGER,  -- 0/1
    folio_no         TEXT,
    risk_profile     TEXT
);

-- ────────────────────────────────────────────
-- Fact: Scheme Performance (annual)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_id                  TEXT REFERENCES dim_fund(fund_id),
    year                     INTEGER,
    return_1y_pct            REAL,
    return_3y_pct            REAL,
    return_5y_pct            REAL,
    benchmark_return_pct     REAL,
    alpha_pct                REAL,
    expense_ratio            REAL,
    expense_ratio_flagged    INTEGER,
    sharpe_ratio             REAL,
    std_dev                  REAL,
    category                 TEXT,
    UNIQUE(fund_id, year)
);

-- ────────────────────────────────────────────
-- Fact: Monthly AUM
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_id        TEXT REFERENCES dim_fund(fund_id),
    month          TEXT NOT NULL,
    aum_cr         REAL,
    net_inflow_cr  REAL,
    UNIQUE(fund_id, month)
);

-- ────────────────────────────────────────────
-- Supporting: SIP Register
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_sip (
    sip_id                      TEXT PRIMARY KEY,
    investor_id                 TEXT REFERENCES dim_investor(investor_id),
    fund_id                     TEXT REFERENCES dim_fund(fund_id),
    sip_amount                  REAL,
    sip_date                    INTEGER,
    start_date                  TEXT,
    frequency                   TEXT,
    total_instalments_completed INTEGER,
    status                      TEXT,
    last_instalment_date        TEXT,
    mandate_amount              REAL
);

-- ────────────────────────────────────────────
-- Supporting: Portfolio Holdings
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_holdings (
    holding_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_id        TEXT REFERENCES dim_fund(fund_id),
    quarter_end    TEXT,
    sector         TEXT,
    allocation_pct REAL,
    num_stocks     INTEGER
);

-- ────────────────────────────────────────────
-- Supporting: Benchmark Returns
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_benchmark (
    bm_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    benchmark          TEXT,
    date               TEXT,
    index_value        REAL,
    daily_return_pct   REAL,
    UNIQUE(benchmark, date)
);
