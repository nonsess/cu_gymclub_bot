from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from src.db.base import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session