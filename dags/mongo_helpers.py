"""
MongoDB helper utilities for the IT Jobs Market ETL pipeline.
Provides connection management, upsert, cleanup, and CSV export functions.
"""

import os
from datetime import datetime, timedelta, timezone

import pandas as pd
from pymongo import MongoClient, UpdateOne


def get_mongo_client() -> MongoClient:
    """Create and return a pymongo client from environment variables."""
    host = os.getenv('MONGO_HOST', 'mongodb')
    port = int(os.getenv('MONGO_PORT', 27017))
    username = os.getenv('MONGO_USERNAME', 'root')
    password = os.getenv('MONGO_PASSWORD', 'rootpassword')
    return MongoClient(
        host=host,
        port=port,
        username=username,
        password=password,
        authSource='admin',
    )


def get_database(db_name: str = None):
    """Return the MongoDB database instance."""
    db_name = db_name or os.getenv('MONGO_DB', 'it_jobs_market')
    client = get_mongo_client()
    return client[db_name]


def upsert_documents(collection_name: str, documents: list, key_field: str = 'source_id') -> int:
    """
    Bulk upsert documents into a MongoDB collection.
    Uses key_field for deduplication (upsert by matching key).
    Returns number of documents processed.
    """
    db = get_database()
    collection = db[collection_name]

    if not documents:
        return 0

    operations = []
    for doc in documents:
        # Remove any existing _id to avoid conflicts on upsert
        doc.pop('_id', None)

        key_value = doc.get(key_field)
        if key_value is not None:
            operations.append(
                UpdateOne(
                    {key_field: key_value},
                    {'$set': doc},
                    upsert=True
                )
            )
        else:
            # No key field — just insert
            collection.insert_one(doc)

    if operations:
        result = collection.bulk_write(operations)
        return result.upserted_count + result.modified_count

    return len(documents)


def delete_expired(collection_name: str, timestamp_field: str = 'inserted_at', days: int = 7) -> int:
    """Delete documents older than `days` from a collection."""
    db = get_database()
    collection = db[collection_name]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = collection.delete_many({timestamp_field: {'$lt': cutoff}})
    return result.deleted_count


def export_collection_to_csv(collection_name: str, output_path: str, query: dict = None) -> int:
    """Export a MongoDB collection to a CSV file. Returns row count."""
    from pathlib import Path

    db = get_database()
    collection = db[collection_name]
    cursor = collection.find(query or {}, {'_id': 0})
    records = list(cursor)

    if not records:
        print(f"⚠️  No records found in {collection_name}")
        return 0

    df = pd.DataFrame(records)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8')
    return len(df)
