-- ============================================================
-- Bluestock MF Analytics – 10 Business Queries (SQLite)
-- ============================================================

-- Q1: Top 5 funds by latest AUM (most recent month)
SELECT
    f.fund_id,
    f.scheme_name,
    f.category,
    a.month,
    a.aum_cr
FROM fact_aum a
JOIN dim_fund f ON a.fund_id = f.fund_id
WHERE a.month = (SELECT MAX(month) FROM fact_aum)
ORDER BY a.aum_cr DESC
LIMIT 5;

-- ─────────────────────────────────────────────────────────────

-- Q2: Average monthly NAV per fund for 2025
SELECT
    fund_id,
    SUBSTR(date, 1, 7)  AS month,
    ROUND(AVG(nav), 4)  AS avg_nav
FROM fact_nav
WHERE date LIKE '2025%'
GROUP BY fund_id, month
ORDER BY fund_id, month;

-- ─────────────────────────────────────────────────────────────

-- Q3: Total SIP inflows by year (YoY growth)
SELECT
    SUBSTR(txn_date, 1, 4)         AS year,
    ROUND(SUM(amount) / 1e7, 2)    AS sip_inflow_cr,
    COUNT(*)                        AS num_transactions
FROM fact_transactions
WHERE txn_type = 'Sip'
GROUP BY year
ORDER BY year;

-- ─────────────────────────────────────────────────────────────

-- Q4: SIP milestone – Dec 2025 monthly SIP inflows
SELECT
    txn_month,
    ROUND(SUM(amount) / 1e7, 2)  AS total_sip_cr,
    COUNT(DISTINCT investor_id)   AS unique_investors,
    COUNT(*)                       AS num_sips
FROM fact_transactions
WHERE txn_type = 'Sip'
  AND txn_month BETWEEN '2025-01' AND '2025-12'
GROUP BY txn_month
ORDER BY txn_month;

-- ─────────────────────────────────────────────────────────────

-- Q5: Fund performance ranking by 1-year return (latest year)
SELECT
    p.fund_id,
    f.scheme_name,
    f.category,
    p.year,
    p.return_1y_pct,
    p.benchmark_return_pct,
    p.alpha_pct,
    p.sharpe_ratio,
    RANK() OVER (ORDER BY p.return_1y_pct DESC) AS perf_rank
FROM fact_performance p
JOIN dim_fund f ON p.fund_id = f.fund_id
WHERE p.year = (SELECT MAX(year) FROM fact_performance)
ORDER BY perf_rank;

-- ─────────────────────────────────────────────────────────────

-- Q6: T30 vs B30 city-tier analysis – total investment and investor count
SELECT
    city_tier,
    txn_type,
    COUNT(DISTINCT investor_id)        AS unique_investors,
    COUNT(*)                            AS num_transactions,
    ROUND(SUM(amount) / 1e7, 2)        AS total_invested_cr
FROM fact_transactions
GROUP BY city_tier, txn_type
ORDER BY city_tier, total_invested_cr DESC;

-- ─────────────────────────────────────────────────────────────

-- Q7: AUM growth trend – total industry AUM per month (2024-2026)
SELECT
    month,
    ROUND(SUM(aum_cr), 2)          AS total_aum_cr,
    ROUND(SUM(net_inflow_cr), 2)   AS total_net_inflow_cr
FROM fact_aum
WHERE month >= '2024-01'
GROUP BY month
ORDER BY month;

-- ─────────────────────────────────────────────────────────────

-- Q8: Investor demographics – age-band breakdown of SIP participation
SELECT
    CASE
        WHEN d.age BETWEEN 18 AND 30 THEN '18-30'
        WHEN d.age BETWEEN 31 AND 45 THEN '31-45'
        WHEN d.age BETWEEN 46 AND 60 THEN '46-60'
        ELSE '60+'
    END                                 AS age_band,
    d.gender,
    COUNT(DISTINCT t.investor_id)        AS investors,
    ROUND(SUM(t.amount) / 1e7, 2)       AS total_sip_cr
FROM fact_transactions t
JOIN dim_investor d ON t.investor_id = d.investor_id
WHERE t.txn_type = 'Sip'
GROUP BY age_band, d.gender
ORDER BY age_band, d.gender;

-- ─────────────────────────────────────────────────────────────

-- Q9: Top 10 sectors by average allocation across equity funds (latest quarter)
SELECT
    h.sector,
    ROUND(AVG(h.allocation_pct), 2) AS avg_allocation_pct,
    SUM(h.num_stocks)               AS total_stocks
FROM fact_holdings h
WHERE h.quarter_end = (SELECT MAX(quarter_end) FROM fact_holdings)
GROUP BY h.sector
ORDER BY avg_allocation_pct DESC
LIMIT 10;

-- ─────────────────────────────────────────────────────────────

-- Q10: Funds with consistently high expense ratios vs category average
SELECT
    f.fund_id,
    f.scheme_name,
    f.category,
    ROUND(AVG(p.expense_ratio), 2)   AS avg_expense_ratio,
    ROUND(
        AVG(p.expense_ratio) - (
            SELECT AVG(p2.expense_ratio)
            FROM fact_performance p2
            JOIN dim_fund f2 ON p2.fund_id = f2.fund_id
            WHERE f2.category = f.category
        ), 2
    )                                 AS vs_category_avg,
    SUM(p.expense_ratio_flagged)      AS times_flagged
FROM fact_performance p
JOIN dim_fund f ON p.fund_id = f.fund_id
GROUP BY f.fund_id, f.scheme_name, f.category
ORDER BY avg_expense_ratio DESC;
