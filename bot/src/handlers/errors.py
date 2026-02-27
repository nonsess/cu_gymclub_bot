import logging
from aiogram import Router
from aiogram.types import ErrorEvent
from httpx import HTTPStatusError

router = Router()
logger = logging.getLogger(__name__)

@router.errors()
async def handle_errors(event: ErrorEvent):
    exception = event.exception
    update = event.update

    error_message = "К сожалению, что-то пошло не по плану :(\n\nНо мы уже работаем над решением проблемы, возвращайся позже"
    
    if isinstance(exception, HTTPStatusError):
        logger.error(f"HTTP ошибка: {exception.response.status_code} - {exception.response.text}")
        
        if update.message:
            await update.message.answer(error_message)
        elif update.callback_query:
            await update.callback_query.answer(error_message, show_alert=True)
        return True

    logger.exception("Необработанная ошибка:", exc_info=exception)
    
    try:
        if update.message:
            await update.message.answer(error_message)
        elif update.callback_query:
            await update.callback_query.answer(error_message, show_alert=True)
    except Exception as e:
        logger.error(f"Критический сбой при ответе пользователю: {e}")
    
    return True
