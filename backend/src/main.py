from fastapi import FastAPI

from src.core.exception_handler import register_exception_handlers
from src.api.api_v1 import router
from src.core.lifespan import lifespan
from src.middlewares.logging_middleware import LoggingMiddleware

app = FastAPI(
    title="CU GYMClub API",
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)

register_exception_handlers(app)

app.include_router(router)