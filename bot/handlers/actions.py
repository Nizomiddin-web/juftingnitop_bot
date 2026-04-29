"""Yoqtirish, saqlash, bloklash, shikoyat — kichik harakatlar."""
import logging

from aiogram import F, Router, types
from sqlalchemy import and_, delete, func, select

from bot.database.engine import async_session
from bot.database.models import (
    Block,
    Favorite,
    Like,
    MatchRequest,
    RequestStatus,
    User,
    UserReport,
)
from bot.keyboards.inline import generate_report_reasons_kb

router = Router()


AUTO_BAN_THRESHOLD = 3


# --- LIKE / MUTUAL MATCH ---


@router.callback_query(F.data.startswith("like_"))
async def like_candidate(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    sender_id = call.from_user.id
    if target_id == sender_id:
        return await call.answer("O'zingizni yoqtirib bo'lmaydi.", show_alert=True)

    async with async_session() as session:
        # Allaqachon yoqtirganmi?
        existing = (
            await session.execute(
                select(Like).where(and_(Like.from_id == sender_id, Like.to_id == target_id))
            )
        ).scalars().first()
        if existing:
            return await call.answer("Siz allaqachon yoqtirgansiz.")

        session.add(Like(from_id=sender_id, to_id=target_id))

        # O'zaro yoqtirish bormi?
        mutual = (
            await session.execute(
                select(Like).where(and_(Like.from_id == target_id, Like.to_id == sender_id))
            )
        ).scalars().first()
        await session.commit()

        sender = (await session.execute(select(User).filter_by(telegram_id=sender_id))).scalars().first()
        target = (await session.execute(select(User).filter_by(telegram_id=target_id))).scalars().first()

    if mutual:
        try:
            await call.bot.send_message(
                target_id,
                f"💞 <b>O'zaro yoqtirish!</b>\n"
                f"<b>{sender.full_name if sender else 'Nomzod'}</b> sizni yoqtirdi va siz uni yoqtirgansiz.\n"
                f"Endi tanishuv so'rovini yuboring.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await call.answer("💞 O'zaro yoqtirish! Endi so'rov yuboring.", show_alert=True)
    else:
        if target and target.notifications_on:
            try:
                await call.bot.send_message(
                    target_id,
                    "❤️ Sizni kimdir yoqtirdi! '💌 So'rovlar' bo'limini tekshiring.",
                )
            except Exception:
                pass
        await call.answer("❤️ Yoqtirildi.")


# --- SAVE / FAVORITES ---


@router.callback_query(F.data.startswith("save_"))
async def save_candidate(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    user_id = call.from_user.id
    if target_id == user_id:
        return await call.answer()

    async with async_session() as session:
        existing = (
            await session.execute(
                select(Favorite).where(
                    and_(Favorite.user_id == user_id, Favorite.target_id == target_id)
                )
            )
        ).scalars().first()
        if existing:
            return await call.answer("Allaqachon saqlangan.")
        session.add(Favorite(user_id=user_id, target_id=target_id))
        await session.commit()
    await call.answer("⭐ Saqlandi.")


# --- BLOCK ---


@router.callback_query(F.data.startswith("block_"))
async def block_candidate(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[1])
    user_id = call.from_user.id
    if target_id == user_id:
        return await call.answer()

    async with async_session() as session:
        existing = (
            await session.execute(
                select(Block).where(
                    and_(Block.user_id == user_id, Block.target_id == target_id)
                )
            )
        ).scalars().first()
        if existing:
            return await call.answer("Allaqachon bloklangan.")
        session.add(Block(user_id=user_id, target_id=target_id))
        # Mavjud so'rov/aktiv tanishuv ham yopilsin
        await session.execute(
            delete(MatchRequest).where(
                ((MatchRequest.sender_id == user_id) & (MatchRequest.receiver_id == target_id))
                | ((MatchRequest.sender_id == target_id) & (MatchRequest.receiver_id == user_id))
            )
        )
        await session.commit()
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer("🚫 Bloklandi. Bu nomzodni boshqa ko'rmaysiz.", show_alert=True)


# --- REPORT user (with reasons) ---


@router.callback_query(F.data.startswith("report_") & ~F.data.startswith("reportr_"))
async def report_candidate(call: types.CallbackQuery):
    if call.data == "report_cancel":
        try:
            await call.message.delete()
        except Exception:
            pass
        return await call.answer()

    target_id = int(call.data.split("_")[1])
    await call.message.answer(
        "⚠️ Shikoyat sababini tanlang:",
        reply_markup=generate_report_reasons_kb(target_id),
    )
    await call.answer()


@router.callback_query(F.data == "report_cancel")
async def report_cancel(call: types.CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("reportr_"))
async def report_save(call: types.CallbackQuery):
    parts = call.data.split("_")
    target_id = int(parts[1])
    code = parts[2]
    reporter_id = call.from_user.id

    if target_id == reporter_id:
        return await call.answer()

    label_map = {
        "fake": "Soxta anketa",
        "offensive": "Qo'pol muomala",
        "scam": "Aldash / firibgarlik",
        "inappropriate": "Nomaqbul rasm yoki matn",
        "other": "Boshqa",
    }
    reason = label_map.get(code, "Boshqa")

    auto_banned = False
    async with async_session() as session:
        existing = (
            await session.execute(
                select(UserReport).where(
                    and_(
                        UserReport.reporter_id == reporter_id,
                        UserReport.target_id == target_id,
                        UserReport.is_resolved == False,  # noqa
                    )
                )
            )
        ).scalars().first()
        if existing:
            return await call.answer("Siz allaqachon shikoyat qilgansiz.", show_alert=True)

        session.add(UserReport(reporter_id=reporter_id, target_id=target_id, reason=reason))
        await session.commit()

        # Auto-ban tekshiruvi
        n = (
            await session.execute(
                select(func.count())
                .select_from(UserReport)
                .where(
                    and_(
                        UserReport.target_id == target_id,
                        UserReport.is_resolved == False,  # noqa
                    )
                )
            )
        ).scalar() or 0

        if n >= AUTO_BAN_THRESHOLD:
            target = (
                await session.execute(select(User).filter_by(telegram_id=target_id))
            ).scalars().first()
            if target and not target.is_banned:
                target.is_banned = True
                target.is_active = False
                await session.commit()
                auto_banned = True

    try:
        await call.message.edit_text(f"✅ Shikoyatingiz qabul qilindi. Sabab: {reason}")
    except Exception:
        await call.message.answer(f"✅ Shikoyat qabul qilindi. Sabab: {reason}")

    if auto_banned:
        try:
            await call.bot.send_message(
                target_id,
                "⚠️ Sizning anketangiz bir nechta foydalanuvchi tomonidan shikoyat qilindi va "
                "<b>avtomatik banlandi</b>. Adolatsiz deb o'ylasangiz: @juftingnitop_admin",
                parse_mode="HTML",
            )
        except Exception:
            pass
    await call.answer("Yuborildi.")
