import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.config import BOT_TOKEN
from bot.database.engine import init_db
from bot.middlewares.rate_limit import RateLimitMiddleware
from bot.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)


async def main():
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN .env ichida belgilanmagan")
        return

    await init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Rate-limit (admin'larga qo'llanmaydi)
    rate_limit = RateLimitMiddleware(max_events=30, window_sec=60)
    dp.message.middleware(rate_limit)
    dp.callback_query.middleware(rate_limit)

    from bot.handlers import (
        actions,
        admin,
        chat,
        help_center,
        match,
        menu,
        profile,
        registration,
        requests,
        settings,
    )

    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(profile.router)
    dp.include_router(settings.router)
    dp.include_router(help_center.router)
    dp.include_router(actions.router)
    dp.include_router(menu.router)
    dp.include_router(match.router)
    dp.include_router(requests.router)
    dp.include_router(chat.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logging.info("Bot va scheduler ishga tushdi.")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    asyncio.run(main())
