import logging
from aiogram import Router
from aiogram.types import ErrorEvent
from httpx import HTTPStatusError

router = Router()
logger = logging.getLogger(__name__)

@router.errors()
async def handle_http_status_error(event: ErrorEvent):
    exception = event.exception
    
    if isinstance(exception, HTTPStatusError):
        logger.error(f"HTTP ошибка: {exception.response.status_code} - {exception.response.text}")
        
        if event.update.message:
            await event.update.message.answer(
                "⚠️ Временные проблемы. Попробуйте позже."
            )
        elif event.update.callback_query:
            await event.update.callback_query.answer(
                "⚠️ Временные проблемы. Попробуйте позже.", show_alert=True
            )
        
        return True
    
    return False


@router.errors()
async def handle_all_errors(event: ErrorEvent):
    logger.exception(
        "Необработанная ошибка: %s", 
        event.exception, 
        exc_info=event.exception
    )
    
    return True