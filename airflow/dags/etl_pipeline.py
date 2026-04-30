"""
ETL pipeline functions for the IT Jobs Market project.
Each function corresponds to one Airflow DAG task.

Imports and reuses cleaning/normalization logic from the
it-jobs-market project (mounted at /opt/airflow/it-jobs-market).
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ── Add it-jobs-market to Python path so we can import the pipeline ──
IT_JOBS_PATH = Path('/opt/airflow/it-jobs-market')
if str(IT_JOBS_PATH) not in sys.path:
    sys.path.insert(0, str(IT_JOBS_PATH))

# Import shared MongoDB helpers (co-located in dags/)
from mongo_helpers import (
    get_database,
    upsert_documents,
    delete_expired,
    export_collection_to_csv,
)


# ─────────────────────────────────────────────────────────────────────
# TASK 1: Extract raw data → MongoDB
# ─────────────────────────────────────────────────────────────────────
def extract_raw_to_mongodb() -> int:
    """Load raw CSV/JSON files from each source into MongoDB collections.

    Each source gets its own collection to preserve original schema:
      raw_hh, raw_kolesa, raw_kaspi, raw_telegram
    """
    datasets_path = IT_JOBS_PATH / 'datasets IT Jobs'
    total = 0
    def _load_csv_to_collection(file_path: Path, collection_name: str, key_field: str):
        nonlocal total
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path.name}")
            return
        df = pd.read_csv(file_path)
        df['_source_file'] = file_path.name
        df['inserted_at'] = datetime.now(timezone.utc)
        # Convert to list of dicts, handling NaN → None
        records = json.loads(df.to_json(orient='records', date_format='iso'))
        for r in records:
            r['inserted_at'] = datetime.now(timezone.utc)
        upsert_documents(collection_name, records, key_field=key_field)
        total += len(records)
        print(f"✅ {collection_name}: {len(records)} records from {file_path.name}")

    # HH.kz
    for f in sorted(datasets_path.glob('hh_*.csv')):
        _load_csv_to_collection(f, 'raw_hh', key_field='id')

    # Kolesa
    for name in ['kolesa_vacancies.csv', 'kolesa_vacancies_smart.csv']:
        _load_csv_to_collection(datasets_path / name, 'raw_kolesa', key_field='url')

    # Kaspi
    _load_csv_to_collection(
        datasets_path / 'kaspi_it_vacancies_2024.csv', 'raw_kaspi', key_field='URL'
    )

    # Telegram channels (files named like -1001746243221_itcom_kz.csv)
    for f in sorted(datasets_path.glob('-*_*.csv')):
        _load_csv_to_collection(f, 'raw_telegram', key_field='message_id')

    print(f"\n✅ Extract complete — {total} total raw documents loaded")
    return total


# ─────────────────────────────────────────────────────────────────────
# TASK 2: Transform & store unified data in MongoDB
# ─────────────────────────────────────────────────────────────────────
def transform_and_store_unified() -> int:
    """Run the full cleaning/normalization pipeline, then store the
    unified result in the `unified_jobs` MongoDB collection."""

    # Import the pipeline class from the mounted project
    from job_integration_pipeline import JobIntegrationPipeline

    pipeline = JobIntegrationPipeline()

    print("Step 1: Loading data from all sources...")
    pipeline.load_all_sources()

    print("\nStep 2: Cleaning and normalizing data...")
    pipeline.clean_data()

    print("\nStep 3: Extracting structured fields...")
    pipeline.extract_fields()

    print("\nStep 4: Creating final database...")
    pipeline.create_final_database()

    # Optional LLM enrichment
    groq_key = os.getenv('GROQ_API_KEY', '').strip()
    if groq_key:
        try:
            from airflow.models import Variable
            enable_llm = Variable.get(
                'enable_llm_enrichment', default_var='false'
            ).lower() == 'true'
        except Exception:
            enable_llm = False

        if enable_llm:
            print("\nStep 5: Processing with Groq LLM...")
            try:
                pipeline.process_with_groq(limit=50)
            except Exception as e:
                print(f"⚠️  LLM enrichment failed (non-fatal): {e}")
        else:
            print("\nStep 5: LLM disabled (set Airflow Variable 'enable_llm_enrichment' = 'true')")
    else:
        print("\nStep 5: Skipping LLM — no GROQ_API_KEY set")

    # Also run the legacy CSV export (for Streamlit compatibility)
# Step 5b — around line 123-127 in etl_pipeline.py
    print("\nStep 5b: Running legacy CSV/SQLite export...")
    try:
        pipeline.export()
    except Exception as e:
        print(f"⚠️  Legacy export failed (non-fatal): {e}")

    # Store unified data in MongoDB
    print("\nStep 6: Storing unified data in MongoDB...")
    if pipeline.final_db is None or pipeline.final_db.empty:
        print("⚠️  No data to store")
        return 0

    df = pipeline.final_db.copy()
    df['inserted_at'] = datetime.now(timezone.utc)

    # Convert timestamps to strings for MongoDB serialization
    for col in ['posted_at', 'scraped_at']:
        if col in df.columns:
            df[col] = df[col].astype(str)

    # Replace NaN with None (MongoDB-friendly)
    df = df.where(pd.notnull(df), None)
    records = df.to_dict('records')

    # Ensure inserted_at is a real datetime for TTL queries
    for r in records:
        r['inserted_at'] = datetime.now(timezone.utc)

    upsert_documents('unified_jobs', records, key_field='id')
    print(f"✅ Stored {len(records)} unified job records in MongoDB")

    return len(records)


# ─────────────────────────────────────────────────────────────────────
# TASK 3: Export CSV for Streamlit dashboard
# ─────────────────────────────────────────────────────────────────────
def export_csvs() -> int:
    """Export unified data from MongoDB to CSV files
    that the Streamlit dashboard can read."""
    data_dir = IT_JOBS_PATH / 'data'

    csv_path = data_dir / 'interim' / 'unified_job_database.csv'
    count = export_collection_to_csv('unified_jobs', str(csv_path))
    print(f"✅ Exported {count} records to {csv_path.name}")

    return count


# ─────────────────────────────────────────────────────────────────────
# TASK 4: Cleanup expired data (>7 days)
# ─────────────────────────────────────────────────────────────────────
def cleanup_old_data(days: int = 7) -> int:
    """Remove records older than `days` from all MongoDB collections."""
    collections = [
        ('raw_hh', 'inserted_at'),
        ('raw_kolesa', 'inserted_at'),
        ('raw_kaspi', 'inserted_at'),
        ('raw_telegram', 'inserted_at'),
        ('unified_jobs', 'inserted_at'),
    ]

    total_deleted = 0
    for coll_name, ts_field in collections:
        deleted = delete_expired(coll_name, timestamp_field=ts_field, days=days)
        if deleted > 0:
            print(f"🗑️  Deleted {deleted} expired records from {coll_name}")
        total_deleted += deleted

    print(f"\n✅ Cleanup complete — {total_deleted} expired records removed")
    return total_deleted
