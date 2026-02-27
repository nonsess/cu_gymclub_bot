from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.scripts.seed_data import seed_on_startup
from backend.src.services.cache import action_cache
from src.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.CREATE_SEED_DATA:
        await seed_on_startup()
    
    yield

    await action_cache.close()