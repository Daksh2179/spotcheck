CREATE TABLE IF NOT EXISTS gold_sector_patterns (
    id SERIAL PRIMARY KEY,
    sector VARCHAR(100),
    transaction_type VARCHAR(10),
    avg_pct_change_2d NUMERIC,
    avg_pct_change_30d NUMERIC,
    total_trades INTEGER,
    total_trade_value NUMERIC,
    period_month DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gold_top_insiders (
    id SERIAL PRIMARY KEY,
    insider_name VARCHAR(255),
    insider_title VARCHAR(255),
    company_name VARCHAR(255),
    ticker VARCHAR(10),
    total_trades INTEGER,
    avg_pct_change_30d NUMERIC,
    total_trade_value NUMERIC,
    win_rate NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gold_monthly_trends (
    id SERIAL PRIMARY KEY,
    period_month DATE,
    total_buys INTEGER,
    total_sells INTEGER,
    avg_pct_change_30d_buys NUMERIC,
    avg_pct_change_30d_sells NUMERIC,
    total_trade_value NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);