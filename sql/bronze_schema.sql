CREATE TABLE IF NOT EXISTS bronze_sec_filings (
    id SERIAL PRIMARY KEY,
    accession_number VARCHAR(25),
    filed_date DATE,
    company_name VARCHAR(255),
    ticker VARCHAR(10),
    cik VARCHAR(20),
    insider_name VARCHAR(255),
    insider_title VARCHAR(255),
    transaction_type VARCHAR(10),
    transaction_date DATE,
    shares_traded NUMERIC,
    price_per_share NUMERIC,
    shares_owned_after NUMERIC,
    raw_json TEXT,
    ingested_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bronze_stock_prices (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10),
    price_date DATE,
    open_price NUMERIC,
    close_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    volume BIGINT,
    ingested_at TIMESTAMP DEFAULT NOW()
);