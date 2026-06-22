import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings   # ✅ use centralized config

# Concurrency control
DB_CONCURRENCY_LIMIT = 100
db_semaphore = asyncio.Semaphore(DB_CONCURRENCY_LIMIT)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=50,
    max_overflow=100,
    pool_timeout=10,
    pool_recycle=1800,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

async def get_db():
    async with db_semaphore:
        async with AsyncSessionLocal() as session:
            yield session