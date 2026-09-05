-- ============================================================
-- Bluestock MF Analytics – 10 Business Queries (Real Dataset)
-- ============================================================

-- Q1: Top 5 fund houses by latest AUM
SELECT fund_house,
       ROUND(SUM(aum_crore), 0)  AS total_aum_crore,
       SUM(num_schemes)           AS total_schemes
FROM fact_aum
WHERE date = (SELECT MAX(date) FROM fact_aum)
GROUP BY fund_house
ORDER BY total_aum_crore DESC
LIMIT 5;

-- ─────────────────────────────────────────────────────────────

-- Q2: Monthly industry SIP inflow trend (2022–2025)
SELECT month,
       sip_inflow_crore,
       active_sip_accounts_crore,
       ROUND(yoy_growth_pct, 1) AS yoy_pct
FROM fact_sip_inflows
ORDER BY month;

-- ─────────────────────────────────────────────────────────────

-- Q3: Top 10 schemes by 1-year return
SELECT f.scheme_name, f.fund_house, f.category,
       p.return_1yr_pct, p.sharpe_ratio, p.aum_crore,
       p.morningstar_rating
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.return_1yr_pct DESC
LIMIT 10;

-- ─────────────────────────────────────────────────────────────

-- Q4: Category-wise net inflows (latest 6 months)
SELECT category,
       ROUND(SUM(net_inflow_crore), 0) AS total_net_inflow_crore
FROM fact_category_inflows
WHERE month >= (SELECT SUBSTR(MAX(month),1,4) || '-' ||
                PRINTF('%02d', CAST(SUBSTR(MAX(month),6,2) AS INTEGER) - 5)
                FROM fact_category_inflows)
GROUP BY category
ORDER BY total_net_inflow_crore DESC;

-- ─────────────────────────────────────────────────────────────

-- Q5: Fund performance ranking — alpha vs benchmark
SELECT f.scheme_name, f.fund_house, f.category,
       p.return_1yr_pct, p.benchmark_3yr_pct,
       p.alpha, p.beta, p.sharpe_ratio,
       RANK() OVER (ORDER BY p.alpha DESC) AS alpha_rank
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY alpha_rank;

-- ─────────────────────────────────────────────────────────────

-- Q6: T30 vs B30 transaction analysis
SELECT city_tier,
       transaction_type,
       COUNT(*)                              AS num_txns,
       ROUND(SUM(amount_inr) / 1e7, 2)      AS total_cr,
       COUNT(DISTINCT investor_id)           AS unique_investors
FROM fact_transactions
GROUP BY city_tier, transaction_type
ORDER BY city_tier, total_cr DESC;

-- ─────────────────────────────────────────────────────────────

-- Q7: Age group SIP analysis
SELECT age_group,
       COUNT(*)                         AS num_sip_txns,
       ROUND(AVG(amount_inr), 0)        AS avg_sip_amount,
       ROUND(SUM(amount_inr) / 1e7, 2)  AS total_cr
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY age_group
ORDER BY age_group;

-- ─────────────────────────────────────────────────────────────

-- Q8: Top 10 sectors by total portfolio weight (latest holdings)
SELECT sector,
       ROUND(AVG(weight_pct), 2)        AS avg_weight_pct,
       ROUND(SUM(market_value_cr), 0)   AS total_mkt_value_cr,
       COUNT(DISTINCT stock_symbol)     AS num_stocks
FROM fact_holdings
WHERE portfolio_date = (SELECT MAX(portfolio_date) FROM fact_holdings)
GROUP BY sector
ORDER BY avg_weight_pct DESC
LIMIT 10;

-- ─────────────────────────────────────────────────────────────

-- Q9: Industry folio count growth
SELECT month, total_folios_crore,
       equity_folios_crore,
       ROUND(equity_folios_crore / total_folios_crore * 100, 1) AS equity_share_pct
FROM fact_folio_count
ORDER BY month;

-- ─────────────────────────────────────────────────────────────

-- Q10: State-wise transaction volumes (top 10 states)
SELECT state,
       COUNT(*)                             AS num_txns,
       ROUND(SUM(amount_inr) / 1e7, 2)     AS total_cr,
       COUNT(DISTINCT investor_id)          AS unique_investors
FROM fact_transactions
GROUP BY state
ORDER BY total_cr DESC
LIMIT 10;
