from fastapi import FastAPI

from src.core.exception_handler import register_exception_handlers
from src.api.api_v1 import router

app = FastAPI(
    title="CU GYMClub API",
)

register_exception_handlers(app)
app.include_router(router)