import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.db import execute_query

def build_sector_patterns():
    print("Building gold_sector_patterns...")
    
    truncate = "TRUNCATE TABLE gold_sector_patterns"
    execute_query(truncate)

    query = """
        INSERT INTO gold_sector_patterns
        (sector, transaction_type, avg_pct_change_2d, avg_pct_change_30d,
         total_trades, total_trade_value, period_month)
        SELECT
            COALESCE(ticker, 'Unknown') as sector,
            CASE WHEN is_buy THEN 'BUY' ELSE 'SELL' END as transaction_type,
            ROUND(AVG(pct_change_2d)::numeric, 4) as avg_pct_change_2d,
            ROUND(AVG(pct_change_30d)::numeric, 4) as avg_pct_change_30d,
            COUNT(*) as total_trades,
            ROUND(SUM(trade_value)::numeric, 2) as total_trade_value,
            DATE_TRUNC('month', transaction_date)::date as period_month
        FROM silver_insider_trades
        WHERE pct_change_30d IS NOT NULL
        GROUP BY ticker, is_buy, DATE_TRUNC('month', transaction_date)
    """
    execute_query(query)
    print("gold_sector_patterns built")

def build_top_insiders():
    print("Building gold_top_insiders...")
    
    truncate = "TRUNCATE TABLE gold_top_insiders"
    execute_query(truncate)

    query = """
        INSERT INTO gold_top_insiders
        (insider_name, insider_title, company_name, ticker,
         total_trades, avg_pct_change_30d, total_trade_value, win_rate)
        SELECT
            insider_name,
            insider_title,
            company_name,
            ticker,
            COUNT(*) as total_trades,
            ROUND(AVG(pct_change_30d)::numeric, 4) as avg_pct_change_30d,
            ROUND(SUM(trade_value)::numeric, 2) as total_trade_value,
            ROUND(
                (SUM(CASE WHEN (is_buy AND pct_change_30d > 0) 
                          OR (NOT is_buy AND pct_change_30d < 0) 
                          THEN 1 ELSE 0 END)::numeric / COUNT(*)) * 100
            , 2) as win_rate
        FROM silver_insider_trades
        WHERE pct_change_30d IS NOT NULL
        AND insider_name IS NOT NULL
        GROUP BY insider_name, insider_title, company_name, ticker
        HAVING COUNT(*) >= 1
        ORDER BY win_rate DESC
    """
    execute_query(query)
    print("gold_top_insiders built")

def build_monthly_trends():
    print("Building gold_monthly_trends...")
    
    truncate = "TRUNCATE TABLE gold_monthly_trends"
    execute_query(truncate)

    query = """
        INSERT INTO gold_monthly_trends
        (period_month, total_buys, total_sells,
         avg_pct_change_30d_buys, avg_pct_change_30d_sells, total_trade_value)
        SELECT
            DATE_TRUNC('month', transaction_date)::date as period_month,
            SUM(CASE WHEN is_buy THEN 1 ELSE 0 END) as total_buys,
            SUM(CASE WHEN NOT is_buy THEN 1 ELSE 0 END) as total_sells,
            ROUND(AVG(CASE WHEN is_buy THEN pct_change_30d END)::numeric, 4) as avg_pct_change_30d_buys,
            ROUND(AVG(CASE WHEN NOT is_buy THEN pct_change_30d END)::numeric, 4) as avg_pct_change_30d_sells,
            ROUND(SUM(trade_value)::numeric, 2) as total_trade_value
        FROM silver_insider_trades
        WHERE pct_change_30d IS NOT NULL
        GROUP BY DATE_TRUNC('month', transaction_date)
        ORDER BY period_month
    """
    execute_query(query)
    print("gold_monthly_trends built")

def run():
    build_sector_patterns()
    build_top_insiders()
    build_monthly_trends()
    print("All gold tables built successfully")

if __name__ == "__main__":
    run()