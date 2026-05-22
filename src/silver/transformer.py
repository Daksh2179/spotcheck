import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.db import execute_query

def get_bronze_filings():
    query = """
        SELECT 
            accession_number,
            filed_date,
            company_name,
            ticker,
            insider_name,
            insider_title,
            transaction_type,
            transaction_date,
            shares_traded,
            price_per_share,
            shares_owned_after
        FROM bronze_sec_filings
        WHERE ticker IS NOT NULL
        AND ticker != ''
        AND ingested_at >= NOW() - INTERVAL '2 days'
    """
    return execute_query(query, fetch=True)

def get_price_on_date(ticker, target_date, direction="after", days=2):
    if direction == "before":
        query = """
            SELECT close_price, price_date
            FROM bronze_stock_prices
            WHERE ticker = %s
            AND price_date <= %s
            ORDER BY price_date DESC
            LIMIT 1
        """
        params = (ticker, target_date - timedelta(days=days))
    else:
        query = """
            SELECT close_price, price_date
            FROM bronze_stock_prices
            WHERE ticker = %s
            AND price_date >= %s
            ORDER BY price_date ASC
            LIMIT 1
        """
        params = (ticker, target_date + timedelta(days=days))

    result = execute_query(query, params, fetch=True)
    if result:
        return float(result[0]["close_price"])
    return None

def calculate_pct_change(price_before, price_after):
    if price_before and price_after and price_before != 0:
        return round(((price_after - price_before) / price_before) * 100, 4)
    return None

def transform_and_store():
    filings = get_bronze_filings()
    if not filings:
        print("No filings to transform")
        return

    print(f"Transforming {len(filings)} filings...")
    stored = 0

    for filing in filings:
        try:
            ticker = filing["ticker"]
            transaction_date = filing["transaction_date"]
            filed_date = filing["filed_date"]

            if not transaction_date or not ticker:
                continue

            price_per_share = float(filing["price_per_share"]) if filing["price_per_share"] else None
            shares_traded = float(filing["shares_traded"]) if filing["shares_traded"] else None
            trade_value = round(price_per_share * shares_traded, 2) if price_per_share and shares_traded else None

            price_2d_before = get_price_on_date(ticker, transaction_date, direction="before", days=2)
            price_2d_after = get_price_on_date(ticker, transaction_date, direction="after", days=2)
            price_30d_after = get_price_on_date(ticker, transaction_date, direction="after", days=30)

            pct_change_2d = calculate_pct_change(price_2d_before, price_2d_after)
            pct_change_30d = calculate_pct_change(price_2d_before, price_30d_after)

            transaction_type = filing.get("transaction_type")
            is_buy = True if transaction_type in ["P", "A"] else True if transaction_type is None else False

            query = """
                INSERT INTO silver_insider_trades
                (accession_number, filed_date, company_name, ticker,
                 insider_name, insider_title, transaction_type, transaction_date,
                 shares_traded, price_per_share, shares_owned_after, trade_value,
                 price_2d_before, price_2d_after, price_30d_after,
                 pct_change_2d, pct_change_30d, is_buy)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """
            params = (
                filing["accession_number"],
                filed_date,
                filing["company_name"],
                ticker,
                filing["insider_name"],
                filing["insider_title"],
                filing["transaction_type"],
                transaction_date,
                shares_traded,
                price_per_share,
                float(filing["shares_owned_after"]) if filing["shares_owned_after"] else None,
                trade_value,
                price_2d_before,
                price_2d_after,
                price_30d_after,
                pct_change_2d,
                pct_change_30d,
                is_buy
            )
            execute_query(query, params)
            stored += 1

        except Exception as e:
            print(f"Error transforming filing {filing.get('accession_number')}: {e}")
            continue

    print(f"Stored {stored} records in silver layer")
    return stored

def run():
    transform_and_store()

if __name__ == "__main__":
    run()