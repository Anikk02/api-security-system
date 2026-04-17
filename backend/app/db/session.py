import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Concurrency control
DB_CONCURRENCY_LIMIT = 100
db_semaphore = asyncio.Semaphore(DB_CONCURRENCY_LIMIT)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=50,
    max_overflow=100,
    pool_timeout=10,
    pool_recycle=1800,
    pool_pre_ping=True,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

async def get_db():
    async with db_semaphore:
        async with AsyncSessionLocal() as session:
            yield session