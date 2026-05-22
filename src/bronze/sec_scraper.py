import requests
import json
import re
from datetime import datetime, timedelta
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.db import execute_query
from dotenv import load_dotenv
load_dotenv()

HEADERS = {
    "User-Agent": os.getenv("SEC_USER_AGENT", "Spotcheck youremail@example.com"),
    "Accept-Encoding": "gzip, deflate",
}

def get_ticker_from_cik(cik):
    try:
        padded_cik = cik.zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        tickers = data.get("tickers", [])
        return tickers[0] if tickers else None
    except Exception as e:
        return None

def fetch_recent_form4(days_back=1):
    all_hits = []
    
    # Fetch in weekly batches going backwards
    end = datetime.today()
    start = end - timedelta(days=7)
    cutoff = datetime.today() - timedelta(days=days_back)
    
    print(f"Fetching Form 4 filings for last {days_back} days in weekly batches...")

    while start >= cutoff and len(all_hits) < 1000:
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        
        url = f"https://efts.sec.gov/LATEST/search-index?forms=4&dateRange=custom&startdt={start_str}&enddt={end_str}&from=0&size=40"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            all_hits.extend(hits)
            print(f"Batch {start_str} to {end_str}: {len(hits)} filings, total: {len(all_hits)}")
        
        end = start
        start = start - timedelta(days=7)
        time.sleep(0.3)

    print(f"Total filings fetched: {len(all_hits)}")
    return all_hits

def parse_and_store_filings(hits):
    stored = 0
    ticker_cache = {}

    for hit in hits:
        try:
            source = hit.get("_source", {})
            accession_number = hit.get("_id", "").split(":")[0]
            filed_date = source.get("file_date")
            transaction_date = source.get("period_ending") or filed_date
            display_names = source.get("display_names", [])
            ciks = source.get("ciks", [])

            company_name = ""
            insider_name = ""
            company_cik = ""
            ticker = None

            for i, name in enumerate(display_names):
                cik = ciks[i] if i < len(ciks) else ""
                if "(Issuer)" in name or any(c.isupper() and c.isalpha() for c in name.split("(")[0].strip()[-3:]):
                    if not company_name:
                        company_name = re.sub(r'\s*\(CIK.*?\)', '', name).strip()
                        company_cik = cik
                else:
                    if not insider_name:
                        insider_name = re.sub(r'\s*\(CIK.*?\)', '', name).strip()

            # Get ticker from cache or API
            if company_cik:
                if company_cik not in ticker_cache:
                    ticker_cache[company_cik] = get_ticker_from_cik(company_cik)
                    time.sleep(0.1)
                ticker = ticker_cache[company_cik]

            # If no company found, try first entry
            if not company_name and display_names:
                company_name = re.sub(r'\s*\(CIK.*?\)', '', display_names[0]).strip()

            query = """
                INSERT INTO bronze_sec_filings 
                (accession_number, filed_date, company_name, ticker, cik,
                 insider_name, insider_title, transaction_type, transaction_date,
                 shares_traded, price_per_share, shares_owned_after, raw_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """
            params = (
                accession_number,
                filed_date,
                company_name,
                ticker,
                company_cik,
                insider_name,
                None,
                None,
                transaction_date,
                None,
                None,
                None,
                json.dumps(source)
            )
            execute_query(query, params)
            stored += 1

        except Exception as e:
            print(f"Error storing filing: {e}")
            continue

    print(f"Stored {stored} filings in bronze layer")
    return stored

def run():
    hits = fetch_recent_form4(days_back=1)
    if hits:
        parse_and_store_filings(hits)
    else:
        print("No filings found")

if __name__ == "__main__":
    run()