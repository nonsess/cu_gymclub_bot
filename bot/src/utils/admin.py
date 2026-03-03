def is_admin(telegram_id: int) -> bool:
    from src.config import settings
    return str(telegram_id) == str(settings.ADMIN_TELEGRAM_ID)