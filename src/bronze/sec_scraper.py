import requests
import json
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.db import execute_query

HEADERS = {
    "User-Agent": "Spotcheck project daksh2179@gmail.com",
    "Accept-Encoding": "gzip, deflate",
}

def get_ticker_from_cik(cik):
    try:
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        tickers = data.get("tickers", [])
        return tickers[0] if tickers else None
    except Exception as e:
        print(f"Could not get ticker for CIK {cik}: {e}")
        return None

def fetch_recent_form4(days_back=1):
    start_date = (datetime.today() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end_date = datetime.today().strftime("%Y-%m-%d")

    url = f"https://efts.sec.gov/LATEST/search-index?q=%22form+4%22&dateRange=custom&startdt={start_date}&enddt={end_date}&forms=4"

    print(f"Calling: {url}")
    
    # Use the correct EDGAR full text search API
    search_url = f"https://efts.sec.gov/LATEST/search-index?forms=4&startdt={start_date}&enddt={end_date}"
    
    # Correct endpoint
    api_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&dateb=&owner=include&count=40&search_text=&output=atom"
    
    response = requests.get(api_url, headers=HEADERS)
    response.raise_for_status()
    
    # Parse atom/XML feed
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.content)
    
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entries = root.findall('atom:entry', ns)
    print(f"Found {len(entries)} filings")
    return entries

def parse_and_store_filings(entries):
    stored = 0
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    for entry in entries:
        try:
            title = entry.find('atom:title', ns)
            title_text = title.text if title is not None else ""
            
            updated = entry.find('atom:updated', ns)
            filed_date = updated.text[:10] if updated is not None else None
            
            link = entry.find('atom:link', ns)
            accession_url = link.get('href') if link is not None else ""
            
            # Extract accession number from URL
            accession_number = ""
            if accession_url:
                parts = accession_url.split('/')
                if len(parts) >= 2:
                    accession_number = parts[-1].replace('-index.htm', '')

            # Parse title: "4 - Company Name (CIK) (Role)"
            # Example: "4 - PureCycle Technologies, Inc. (0001830033) (Issuer)"
            company_name = ""
            cik = ""
            insider_name = ""
            ticker = None
            
            if ' - ' in title_text:
                after_dash = title_text.split(' - ', 1)[1]
                # Extract CIK from parentheses
                import re
                cik_match = re.findall(r'\((\d+)\)', after_dash)
                if cik_match:
                    cik = cik_match[0]
                # Extract role
                role_match = re.findall(r'\((Issuer|Reporting)\)', after_dash)
                role = role_match[0] if role_match else ""
                # Company name is everything before the first (
                company_name = after_dash.split('(')[0].strip()
                # If reporting, it's the insider name
                if role == "Reporting":
                    insider_name = company_name
                    company_name = ""
                elif role == "Issuer" and cik:
                    ticker = get_ticker_from_cik(cik)
                else:
                    ticker = None

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
                cik,
                insider_name,
                None,
                None,
                filed_date,
                None,
                None,
                None,
                json.dumps({"title": title_text, "url": accession_url})
            )
            execute_query(query, params)
            stored += 1
        except Exception as e:
            print(f"Error storing filing: {e}")
            continue
    
    print(f"Stored {stored} filings in bronze layer")
    return stored

def run():
    entries = fetch_recent_form4(days_back=1)
    if entries:
        parse_and_store_filings(entries)
    else:
        print("No filings found")

if __name__ == "__main__":
    run()