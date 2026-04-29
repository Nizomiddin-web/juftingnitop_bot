from aiogram import F, Router, types
from sqlalchemy import and_, func, or_, select

from bot.database.engine import async_session
from bot.database.models import (
    Favorite,
    Like,
    MatchRequest,
    ProfileView,
    RequestStatus,
    User,
)
from bot.keyboards.inline import generate_request_action_kb

router = Router()


@router.message(F.text == "💬 Tanishuvlar")
async def show_chats(message: types.Message):
    uid = message.from_user.id
    async with async_session() as session:
        active_res = await session.execute(
            select(MatchRequest).where(
                and_(
                    or_(MatchRequest.sender_id == uid, MatchRequest.receiver_id == uid),
                    MatchRequest.status == RequestStatus.ACCEPTED,
                )
            )
        )
        active = active_res.scalars().all()

        finished_res = await session.execute(
            select(MatchRequest).where(
                and_(
                    or_(MatchRequest.sender_id == uid, MatchRequest.receiver_id == uid),
                    MatchRequest.status == RequestStatus.FINISHED,
                )
            )
        )
        finished = finished_res.scalars().all()

        if not active and not finished:
            return await message.answer(
                "💬 <b>Tanishuvlar</b>\n\n"
                "Hozircha tanishuv yo'q.\n"
                "Mos nomzodni toping va muloqotni boshlang.\n"
                "Har bir tanishuv — nikoh sari qadam.",
                parse_mode="HTML",
            )

        text = "💬 <b>Tanishuvlar</b>\n\n"
        if active:
            text += "<b>🟢 Faol:</b>\n"
            for r in active:
                partner_id = r.receiver_id if r.sender_id == uid else r.sender_id
                p_res = await session.execute(select(User).filter_by(telegram_id=partner_id))
                partner = p_res.scalars().first()
                name = partner.full_name if partner else "Noma'lum"
                text += f"• {name} — /yakunlash buyrug'i orqali tugating\n"
        if finished:
            text += "\n<b>📕 Yakunlangan:</b>\n"
            for r in finished[-5:]:
                partner_id = r.receiver_id if r.sender_id == uid else r.sender_id
                p_res = await session.execute(select(User).filter_by(telegram_id=partner_id))
                partner = p_res.scalars().first()
                name = partner.full_name if partner else "Noma'lum"
                text += f"• {name}\n"

        await message.answer(text, parse_mode="HTML")


@router.message(F.text == "💌 So'rovlar")
async def show_requests(message: types.Message):
    uid = message.from_user.id
    async with async_session() as session:
        in_res = await session.execute(
            select(MatchRequest).where(
                and_(
                    MatchRequest.receiver_id == uid,
                    MatchRequest.status == RequestStatus.PENDING,
                )
            )
        )
        incoming = in_res.scalars().all()

        out_res = await session.execute(
            select(MatchRequest).where(
                and_(
                    MatchRequest.sender_id == uid,
                    MatchRequest.status == RequestStatus.PENDING,
                )
            )
        )
        outgoing = out_res.scalars().all()

        if not incoming and not outgoing:
            return await message.answer(
                "💌 <b>So'rovlar</b>\n\n"
                "Hozircha sizga so'rov kelmagan.\n"
                "Nomzodlar sizga tanishuv so'rovi yuborganda bu yerda ko'rinadi.",
                parse_mode="HTML",
            )

        if outgoing:
            await message.answer(
                f"📤 <b>Siz yuborgan: {len(outgoing)} ta</b>\n"
                "Nomzodning javobini kuting.",
                parse_mode="HTML",
            )

        if incoming:
            await message.answer(
                f"📥 <b>Sizga kelgan so'rovlar: {len(incoming)} ta</b>",
                parse_mode="HTML",
            )
            for r in incoming:
                s_res = await session.execute(select(User).filter_by(telegram_id=r.sender_id))
                sender = s_res.scalars().first()
                name = sender.full_name if sender else "Noma'lum"
                txt = (
                    f"💌 <b>{name}</b>\n"
                    f"<b>Xabar:</b> {r.intro_message or '—'}"
                )
                await message.answer(
                    txt,
                    parse_mode="HTML",
                    reply_markup=generate_request_action_kb(r.id),
                )


@router.message(F.text == "⭐ Saqlanganlar")
async def show_favorites(message: types.Message):
    uid = message.from_user.id
    async with async_session() as session:
        res = await session.execute(
            select(Favorite, User)
            .join(User, User.telegram_id == Favorite.target_id)
            .where(Favorite.user_id == uid)
            .order_by(Favorite.id.desc())
            .limit(20)
        )
        rows = res.all()
        if not rows:
            return await message.answer(
                "⭐ <b>Saqlangan nomzodlar</b>\n\nHali hech kim saqlanmagan.",
                parse_mode="HTML",
            )

        text = f"⭐ <b>Saqlanganlar: {len(rows)}</b>\n\n"
        for _, u in rows:
            text += f"• <b>{u.full_name}</b> — {u.region}, {u.district}\n"
        await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📊 Statistikam")
async def show_my_stats(message: types.Message):
    uid = message.from_user.id
    async with async_session() as session:
        views = (
            await session.execute(
                select(func.count()).select_from(ProfileView).where(ProfileView.target_id == uid)
            )
        ).scalar() or 0
        unique_views = (
            await session.execute(
                select(func.count(func.distinct(ProfileView.viewer_id)))
                .select_from(ProfileView)
                .where(ProfileView.target_id == uid)
            )
        ).scalar() or 0
        likes_in = (
            await session.execute(select(func.count()).select_from(Like).where(Like.to_id == uid))
        ).scalar() or 0
        likes_out = (
            await session.execute(select(func.count()).select_from(Like).where(Like.from_id == uid))
        ).scalar() or 0
        req_sent = (
            await session.execute(
                select(func.count()).select_from(MatchRequest).where(MatchRequest.sender_id == uid)
            )
        ).scalar() or 0
        req_in = (
            await session.execute(
                select(func.count()).select_from(MatchRequest).where(MatchRequest.receiver_id == uid)
            )
        ).scalar() or 0
        accepted = (
            await session.execute(
                select(func.count())
                .select_from(MatchRequest)
                .where(
                    and_(
                        or_(MatchRequest.sender_id == uid, MatchRequest.receiver_id == uid),
                        MatchRequest.status.in_([RequestStatus.ACCEPTED, RequestStatus.FINISHED]),
                    )
                )
            )
        ).scalar() or 0
        favorites = (
            await session.execute(
                select(func.count()).select_from(Favorite).where(Favorite.user_id == uid)
            )
        ).scalar() or 0

    text = (
        "📊 <b>Mening statistikam</b>\n\n"
        f"<b>👁 Profilingizga qarashganlar:</b> {views} marta ({unique_views} kishi)\n"
        f"<b>❤️ Sizni yoqtirganlar:</b> {likes_in}\n"
        f"<b>❤️ Siz yoqtirganlar:</b> {likes_out}\n"
        f"<b>💌 Kelgan so'rovlar:</b> {req_in}\n"
        f"<b>📤 Yuborgan so'rovlaringiz:</b> {req_sent}\n"
        f"<b>🤝 Muvaffaqiyatli tanishuvlar:</b> {accepted}\n"
        f"<b>⭐ Saqlanganlar:</b> {favorites}"
    )
    await message.answer(text, parse_mode="HTML")
