import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from sqlalchemy import and_, or_, select

from bot.database.engine import async_session
from bot.database.models import MatchRequest, RequestStatus
from bot.utils.text_filter import filter_reason

router = Router()


MENU_BUTTONS = {
    "👤 Profilim",
    "🤵‍♂️ Nomzodlar",
    "🤵‍♂️ Nomzodlarni ko'rish",
    "💬 Tanishuvlar",
    "💌 So'rovlar",
    "⚙️ Sozlamalar",
    "❓ Yordam",
    "⭐ Saqlanganlar",
    "📊 Statistikam",
    "📍 Joylashuvni yuborish",
    "⏭ Joylashuvsiz davom etish",
    "✅ Yakunlash",
    "🔙 Orqaga",
    "🔙 Viloyatni o'zgartirish",
    "O'tkazib yuborish",
    "Erkak",
    "Ayol",
}


async def get_active_session(user_id: int):
    async with async_session() as session:
        res = await session.execute(
            select(MatchRequest).where(
                and_(
                    or_(MatchRequest.sender_id == user_id, MatchRequest.receiver_id == user_id),
                    MatchRequest.status == RequestStatus.ACCEPTED,
                )
            )
        )
        return res.scalars().first()


@router.message(Command("yakunlash"))
async def end_chat(message: types.Message):
    user_id = message.from_user.id
    async with async_session() as session:
        res = await session.execute(
            select(MatchRequest).where(
                and_(
                    or_(MatchRequest.sender_id == user_id, MatchRequest.receiver_id == user_id),
                    MatchRequest.status == RequestStatus.ACCEPTED,
                )
            )
        )
        req = res.scalars().first()
        if not req:
            return await message.answer("Sizda faol suhbat yo'q.")

        partner_id = req.receiver_id if req.sender_id == user_id else req.sender_id
        req.status = RequestStatus.FINISHED
        await session.commit()

    await message.answer("✅ Suhbat yakunlandi.")
    try:
        await message.bot.send_message(
            partner_id,
            "🛑 Suhbatdoshingiz aloqani yakunladi. Endi u inson bilan suhbatlasha olmaysiz.",
        )
    except Exception:
        pass


@router.message(F.voice)
async def route_voice(message: types.Message):
    user_id = message.from_user.id
    req = await get_active_session(user_id)
    if not req:
        return
    partner_id = req.receiver_id if req.sender_id == user_id else req.sender_id
    try:
        await message.bot.send_voice(
            partner_id,
            voice=message.voice.file_id,
            caption="<i>👤 Nomzod</i>",
            parse_mode="HTML",
            protect_content=True,
        )
    except Exception as e:
        logging.error(f"Voice route failed: {e}")
        await message.answer("Ovoz xabarni yetkazib bo'lmadi.")


@router.message(F.text & ~F.text.startswith("/"))
async def route_anonymous_messages(message: types.Message):
    if message.text in MENU_BUTTONS:
        return

    user_id = message.from_user.id
    req = await get_active_session(user_id)
    if not req:
        return

    reason = filter_reason(message.text)
    if reason:
        return await message.answer(f"❌ {reason}\nXabaringiz nomzodga yetkazilmadi.")

    partner_id = req.receiver_id if req.sender_id == user_id else req.sender_id
    try:
        await message.bot.send_message(
            partner_id,
            f"<i>👤 Nomzod:</i>\n{message.text}",
            parse_mode="HTML",
            protect_content=True,
        )
    except Exception as e:
        logging.error(f"Cannot route message: {e}")
        await message.answer("Xabar yetkazilmadi. Balki foydalanuvchi botni bloklagan.")
