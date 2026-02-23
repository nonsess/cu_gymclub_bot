import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from src.config import settings
from src.handlers import start, swipe, profile, incoming

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def on_startup(bot: Bot):
    logger.info(f"Bot started: @{(await bot.get_me()).username}")

async def on_shutdown(bot: Bot):
    logger.info("Bot shutting down...")
    await bot.session.close()


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_routers(
        start.router,
        swipe.router,
        profile.router,
        incoming.router,
    )
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    return dp


async def main():
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = create_dispatcher()
    
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())