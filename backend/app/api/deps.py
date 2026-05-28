from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal, db_semaphore

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # Dependency for database session with semaphore control
    async with db_semaphore:
        async with AsyncSessionLocal() as session:
            yield session