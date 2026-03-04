from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.scripts.seed_data import seed_on_startup
from src.services.cache import cache
from src.core.config import settings
from src.core.logger import stop_logging, init_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_logging()

    if settings.CREATE_SEED_DATA:
        await seed_on_startup()
    
    yield

    await cache.close()
    stop_logging()