import contextvars
import json
import logging
import logging.handlers
import queue
import re
import sys
from typing import Any, Dict, Optional

from src.core.config import settings

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="system")
telegram_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("telegram_id", default="anon")

class ContextPreservingQueueHandler(logging.handlers.QueueHandler):
    def prepare(self, record: logging.LogRecord) -> Any:
        record.contextvars = {
            "request_id": request_id_var.get(),
            "telegram_id": telegram_id_var.get()
        }
        return super().prepare(record)

class ContextRestoringQueueListener(logging.handlers.QueueListener):
    def handle(self, record: logging.LogRecord) -> None:
        if hasattr(record, "contextvars"):
            context = record.contextvars

            token_id = request_id_var.set(context["request_id"])
            token_telegram_id = telegram_id_var.set(context["telegram_id"])

            try:
                super().handle(record)
            finally:
                request_id_var.reset(token_id)
                telegram_id_var.reset(token_telegram_id)
        else:
            super().handle(record)

class ContextCatchFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.telegram_id = telegram_id_var.get()
        return True

class SensitiveDataFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__()
        self.patterns = {
            "password": re.compile(r'(?i)(password|passwd|pwd)[\'"]?\s*[:=]\s*[\'"]?([^\s,\'"]+)'),
            "token": re.compile(r'(?i)(token|api_key|apikey|secret)[\'"]?\s*[:=]\s*[\'"]?([^\s,\'"]+)'),
            "authorization": re.compile(r"(?i)(authorization:\s*Bearer\s+)([^\s]+)"),
            "phone": re.compile(r"(\+7\d{10})"),
        }

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and record.msg:
            record.msg = self._mask_sensitive_data(str(record.msg))

        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                record.args = self._mask_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        return True

    def _mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        masked_data = {}
        sensitive_keys = {"password", "token", "secret", "api_key", "phone"}

        for key, value in data.items():
            key_lower = str(key).lower()

            if isinstance(value, str):
                if any(sensitive in key_lower for sensitive in sensitive_keys):
                    masked_data[key] = "******"
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            elif isinstance(value, dict):
                masked_data[key] = self._mask_dict(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self._mask_sensitive_data(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        return masked_data

    def _mask_sensitive_data(self, text: str) -> str:
        masked_text = text

        for pattern_name in ["password", "token", "authorization"]:
            if pattern_name in self.patterns:
                masked_text = self.patterns[pattern_name].sub(r"\1******", masked_text)

        if "phone" in self.patterns:
            masked_text = self.patterns["phone"].sub(
                lambda m: m.group(1)[:5] + "***" + m.group(1)[-4:],
                masked_text
            )

        return masked_text

class JSONFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S") + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "unknown"),
            "telegram_id": getattr(record, "telegram_id", "unknown")
        }

        if record.name == "api":
            http_context = self._extract_http_context(record)
            if http_context:
                log_data.update(http_context)

        if record.exc_info:
            error_context = self._extract_error_context(record)
            if error_context:
                log_data.update(error_context)

        extra_data = self._extract_extra_data(record)
        if extra_data:
            log_data["extra"] = extra_data

        try:
            return json.dumps(log_data, ensure_ascii=False)
        except (TypeError, ValueError):
            log_data["message"] = f"Log serialization error: {record.getMessage()}"
            return json.dumps(log_data, ensure_ascii=False, default=str)

    def _extract_http_context(self, record: logging.LogRecord) -> Dict[str, Any]:
        http_context = {}
        http_fields = ["method", "path", "status", "duration_ms"]
        for field in http_fields:
            if hasattr(record, field):
                http_context[field] = getattr(record, field)
        return http_context

    def _extract_error_context(self, record: logging.LogRecord) -> Dict[str, Any]:
        if record.exc_info:
            error_type, error_value, _ = record.exc_info
            error_context = {
                "error": error_type.__name__ if error_type else "UnknownError",
                "message": str(error_value) if error_value else "Unknown error",
            }
            if record.levelno >= logging.ERROR:
                error_context["stack"] = self.formatException(record.exc_info)
            return error_context
        return {}

    def _extract_extra_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        extra_data = {}
        standard_fields = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message", "taskName",
            "request_id", "telegram_id", "method", "path", "status", "duration_ms"
        }
        for key, value in record.__dict__.items():
            if key not in standard_fields and not key.startswith("_"):
                extra_data[key] = value
        return extra_data

_log_queue: Optional[queue.Queue] = None
_queue_handler: Optional[ContextPreservingQueueHandler] = None
_queue_listener: Optional[ContextRestoringQueueListener] = None

def init_logging() -> None:
    global _log_queue, _queue_handler, _queue_listener

    _log_queue = queue.Queue(-1)
    _queue_handler = ContextPreservingQueueHandler(_log_queue)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(_queue_handler)

    handlers = []

    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers.append(stdout_handler)

    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.LOG_FILE_PATH,
            maxBytes=settings.LOG_ROTATE_MB * 1024 * 1024,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8"
        )
        handlers.append(file_handler)
    except (OSError, IOError) as e:
        print(f"Warning: Cannot create file handler: {e}", file=sys.stderr)

    formatter = JSONFormatter()

    sensitive_filter = SensitiveDataFilter()
    context_filter = ContextCatchFilter()

    for handler in handlers:
        handler.setFormatter(formatter)
        handler.addFilter(sensitive_filter)
        handler.addFilter(context_filter)
        handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    _queue_listener = ContextRestoringQueueListener(_log_queue, *handlers, respect_handler_level=True)
    _queue_listener.start()

    logger = logging.getLogger("startup")
    logger.info("Logging initialized", extra={
        "log_level": settings.LOG_LEVEL,
        "log_format": settings.LOG_FORMAT,
        "log_file": settings.LOG_FILE_PATH
    })

def stop_logging() -> None:
    global _queue_listener

    if _queue_listener:
        _queue_listener.stop()
        _queue_listener = None

    logging.getLogger("shutdown").info("Logging stopped")

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def get_api_logger() -> logging.Logger:
    return get_logger("api")

def get_service_logger() -> logging.Logger:
    return get_logger("service")

def get_repo_logger() -> logging.Logger:
    return get_logger("repository")

def get_cache_logger() -> logging.Logger:
    return get_logger("cache")