import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect() -> None:
    global _client, _db
    host = os.getenv("MONGO_HOST", "localhost")
    port = int(os.getenv("MONGO_PORT", "27018"))
    username = os.getenv("MONGO_USERNAME", "root")
    password = os.getenv("MONGO_PASSWORD", "rootpassword")
    db_name = os.getenv("MONGO_DB", "it_jobs_market")

    _client = AsyncIOMotorClient(
        host=host,
        port=port,
        username=username,
        password=password,
        authSource="admin",
    )
    _db = _client[db_name]


async def disconnect() -> None:
    if _client:
        _client.close()


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not connected")
    return _db
