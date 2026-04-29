import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import and_, func, select

from bot.database.engine import async_session
from bot.database.models import Gender, Like, ProfileView, User


async def daily_digest(bot: Bot):
    """Har kuni ertalab faol foydalanuvchilarga statistika va yangi nomzod soni."""
    yesterday = (datetime.now() - timedelta(days=1)).isoformat(sep=" ")
    sent = 0
    failed = 0

    async with async_session() as session:
        users_res = await session.execute(
            select(User).where(
                and_(
                    User.is_active == True,  # noqa
                    User.is_banned == False,  # noqa
                    User.notifications_on == True,  # noqa
                )
            )
        )
        users = users_res.scalars().all()

        for u in users:
            target_gender = Gender.FEMALE if u.gender == Gender.MALE else Gender.MALE

            new_candidates = (
                await session.execute(
                    select(func.count())
                    .select_from(User)
                    .where(
                        and_(
                            User.gender == target_gender,
                            User.is_active == True,  # noqa
                            User.is_banned == False,  # noqa
                            User.created_at >= yesterday,
                        )
                    )
                )
            ).scalar() or 0

            new_views = (
                await session.execute(
                    select(func.count())
                    .select_from(ProfileView)
                    .where(
                        and_(
                            ProfileView.target_id == u.telegram_id,
                            ProfileView.created_at >= yesterday,
                        )
                    )
                )
            ).scalar() or 0

            new_likes = (
                await session.execute(
                    select(func.count())
                    .select_from(Like)
                    .where(and_(Like.to_id == u.telegram_id, Like.created_at >= yesterday))
                )
            ).scalar() or 0

            if new_candidates == 0 and new_views == 0 and new_likes == 0:
                continue

            text = "🌅 <b>Yangiliklar</b>\n\n"
            if new_candidates:
                text += f"🤵 Bugun <b>{new_candidates}</b> ta yangi nomzod qo'shildi\n"
            if new_views:
                text += f"👁 Profilingizga <b>{new_views}</b> marta qarashdi\n"
            if new_likes:
                text += f"❤️ <b>{new_likes}</b> kishi sizni yoqtirdi\n"
            text += "\n👉 Botga kirib ko'ring."

            try:
                await bot.send_message(u.telegram_id, text, parse_mode="HTML")
                sent += 1
            except Exception as e:
                failed += 1
                logging.debug(f"Digest send failed for {u.telegram_id}: {e}")

            # 30 msg/sek limitini hurmat qilish
            if sent % 28 == 0:
                await asyncio.sleep(1)

    logging.info(f"Daily digest: sent={sent}, failed={failed}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    # Har kuni soat 9:00 da
    scheduler.add_job(daily_digest, "cron", hour=9, minute=0, args=[bot])
    return scheduler
