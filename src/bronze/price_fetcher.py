import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.db import execute_query

def fetch_prices_for_ticker(ticker, start_date, end_date):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        if df.empty:
            print(f"No price data found for {ticker}")
            return None
        return df
    except Exception as e:
        print(f"Error fetching prices for {ticker}: {e}")
        return None

def store_prices(ticker, df):
    stored = 0
    for date, row in df.iterrows():
        try:
            query = """
                INSERT INTO bronze_stock_prices
                (ticker, price_date, open_price, close_price, 
                 high_price, low_price, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """
            params = (
                ticker,
                date.date(),
                round(float(row["Open"]), 4),
                round(float(row["Close"]), 4),
                round(float(row["High"]), 4),
                round(float(row["Low"]), 4),
                int(row["Volume"])
            )
            execute_query(query, params)
            stored += 1
        except Exception as e:
            print(f"Error storing price for {ticker} on {date}: {e}")
            continue
    print(f"Stored {stored} price records for {ticker}")
    return stored

def get_tickers_from_bronze():
    query = """
        SELECT DISTINCT ticker 
        FROM bronze_sec_filings 
        WHERE ticker IS NOT NULL 
        AND ticker != ''
        AND ingested_at >= NOW() - INTERVAL '2 days'
    """
    results = execute_query(query, fetch=True)
    return [r["ticker"] for r in results] if results else []

def run():
    tickers = get_tickers_from_bronze()
    if not tickers:
        print("No tickers found in bronze layer")
        return

    print(f"Fetching prices for {len(tickers)} tickers: {tickers}")
    
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=40)).strftime("%Y-%m-%d")
    
    for ticker in tickers:
        df = fetch_prices_for_ticker(ticker, start_date, end_date)
        if df is not None:
            store_prices(ticker, df)

if __name__ == "__main__":
    run()