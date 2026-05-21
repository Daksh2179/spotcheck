from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.bronze.sec_scraper import run as bronze_sec_run
from src.bronze.price_fetcher import run as bronze_price_run
from src.silver.transformer import run as silver_run
from src.gold.aggregator import run as gold_run

default_args = {
    "owner": "spotcheck",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="spotcheck_pipeline",
    default_args=default_args,
    description="Daily insider trading pipeline - Bronze to Gold",
    schedule_interval="0 8 * * 1-5",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["spotcheck", "insider-trading", "medallion"],
) as dag:

    bronze_sec = PythonOperator(
        task_id="bronze_sec_filings",
        python_callable=bronze_sec_run,
    )

    bronze_prices = PythonOperator(
        task_id="bronze_stock_prices",
        python_callable=bronze_price_run,
    )

    silver_transform = PythonOperator(
        task_id="silver_transform",
        python_callable=silver_run,
    )

    gold_aggregate = PythonOperator(
        task_id="gold_aggregate",
        python_callable=gold_run,
    )

    bronze_sec >> bronze_prices >> silver_transform >> gold_aggregate