# Spotcheck

Spotcheck is an automated pipeline that tracks SEC Form 4 insider trading filings and correlates them with subsequent stock price movements.

Corporate insiders (executives, directors, major shareholders) are required to report their stock transactions to the SEC within 2 business days via Form 4 filings. Spotcheck ingests these filings daily, enriches them with market price data, and surfaces patterns in insider behavior over time.

## Architecture

Medallion Architecture batch ETL pipeline orchestrated by Apache Airflow.

**Bronze** — Raw Form 4 filings from SEC EDGAR and stock price history from yfinance

**Silver** — Cleaned and joined dataset with price movement calculations across 2 day and 30 day windows after each transaction

**Gold** — Aggregated analytics tables ready for Power BI dashboard

## Tech Stack

- Python
- PostgreSQL
- Apache Airflow
- Docker
- SEC EDGAR API
- yfinance
- Power BI

## Project Structure

- `dags/` — Airflow DAG defining the Bronze to Silver to Gold pipeline
- `src/bronze/` — SEC EDGAR scraper and yfinance price fetcher
- `src/silver/` — Transformer that cleans filings and calculates price movements
- `src/gold/` — Aggregator that builds analytics ready tables
- `src/db.py` — PostgreSQL connection layer
- `sql/` — Schema definitions for all Bronze, Silver and Gold tables

## Setup

1. Clone the repo and create `.env` from `.env.example`
2. Start PostgreSQL with `docker-compose up -d`
3. Create a Python virtual environment and install dependencies with `pip install -r requirements.txt`
4. Run the SQL schema files in `sql/` to create the tables
5. Initialize Airflow and create an admin user
6. Start Airflow with `airflow standalone`
7. Trigger the pipeline from `http://localhost:8080`

The pipeline runs automatically at 11am on weekdays once Airflow is running.