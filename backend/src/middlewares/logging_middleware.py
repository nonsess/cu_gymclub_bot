import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.core.logger import get_api_logger, request_id_var, telegram_id_var

logger = get_api_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        token_request = request_id_var.set(request_id)

        telegram_id = "anon"
        if "X-Telegram-ID" in request.headers:
            telegram_id = request.headers["X-Telegram-ID"]
        
        token_telegram_id = telegram_id_var.set(telegram_id)

        start_time = time.time()
        is_health_check = request.url.path == "/health"

        try:
            response = await call_next(request)
            if not is_health_check:
                process_time = time.time() - start_time
                logger.info("Request completed", extra={
                    "method": request.method,
                    "path": str(request.url.path),
                    "status": response.status_code,
                    "duration_ms": round(process_time * 1000, 2)
                })
            return response
        except Exception:
            if not is_health_check:
                process_time = time.time() - start_time
                logger.error("Request failed", extra={
                    "method": request.method,
                    "path": str(request.url.path),
                    "duration_ms": round(process_time * 1000, 2)
                }, exc_info=True)
            raise
        finally:
            request_id_var.reset(token_request)
            telegram_id_var.reset(token_telegram_id)