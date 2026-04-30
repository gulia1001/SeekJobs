"""
IT Jobs Market ETL DAG
======================
Daily pipeline that:
  1. Extracts raw job data from CSV/JSON files → MongoDB (raw collections)
  2. Transforms & unifies data using cleaning/normalization logic → MongoDB (unified_jobs)
  3. Exports unified data to CSV for the Streamlit dashboard
  4. Cleans up records older than 7 days

Schedule: Daily at 02:00 UTC
MongoDB collections: raw_hh, raw_kolesa, raw_kaspi, raw_telegram, unified_jobs
"""

from datetime import datetime, timedelta
import logging
from airflow.decorators import dag, task
from etl_pipeline import export_csvs, cleanup_old_data, transform_and_store_unified, extract_raw_to_mongodb 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@dag(
    dag_id='it_jobs_etl',
    description='IT Jobs Market ETL — Extract → Transform → MongoDB + CSV → Cleanup',
    schedule='0 2 * * *',
    start_date=datetime(2026, 4, 1),
    catchup=False,
    default_args={
        'owner': 'airflow',
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
    },
    tags=['etl', 'jobs', 'mongodb'],
)
def it_jobs_etl():

    @task()
    def extract_to_mongodb() -> int:
        """Load raw data files into source-specific MongoDB collections."""
        logger.info("Extracting raw data to MongoDB...")
        from etl_pipeline import extract_raw_to_mongodb
        return extract_raw_to_mongodb()

    @task()
    def transform_and_unify() -> int:
        """Clean, normalize, and store unified data in MongoDB."""
        logger.info("Transforming and unifying data...")
        from etl_pipeline import transform_and_store_unified
        return transform_and_store_unified()

    @task()
    def export_csv() -> int:
        """Export unified data from MongoDB to CSV for Streamlit."""
        logger.info("Exporting unified data to CSV...")
        from etl_pipeline import export_csvs
        return export_csvs()

    @task()
    def cleanup_expired() -> int:
        """Remove records older than 7 days from all collections."""
        logger.info("Cleaning up expired records...")
        from etl_pipeline import cleanup_old_data
        return cleanup_old_data(days=7)

    extract_task = extract_to_mongodb()
    transform_task = transform_and_unify()
    
    extract_task >> transform_task
    transform_task >> [export_csv(), cleanup_expired()]

# Instantiate the DAG
it_jobs_etl()
