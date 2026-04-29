import json
import logging
import math
from datetime import datetime

from aiogram import F, Router, types
from sqlalchemy import and_, or_, select

from bot.database.engine import async_session
from bot.database.models import (
    Block,
    Gender,
    MatchRequest,
    ProfileView,
    RequestStatus,
    User,
    Visibility,
)
from bot.keyboards.inline import generate_candidate_kb

router = Router()


def calculate_age(bdate):
    if not bdate:
        return None
    today = datetime.today().date()
    return today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))


def haversine(lat1, lon1, lat2, lon2):
    if not all([lat1, lon1, lat2, lon2]):
        return 0
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(R * c)


def get_match_percentage(u1: User, u2: User, distance_km: int) -> int:
    score = 100
    if u1.region != u2.region:
        score -= 8
    if u1.intention_period != u2.intention_period:
        score -= 7
    if u1.education_level != u2.education_level:
        score -= 5
    if distance_km > (u1.search_distance_km or 50):
        score -= 15
    elif distance_km > 30:
        score -= 5
    age = calculate_age(u2.birth_date) or 0
    if age and (age < (u1.search_age_min or 18) or age > (u1.search_age_max or 80)):
        score -= 20
    return max(40, min(score, 99))


def _match_reasons(u1: User, u2: User, distance_km: int) -> list[str]:
    reasons = []
    if u1.region == u2.region:
        reasons.append("Hudud mos")
    age = calculate_age(u2.birth_date)
    if age and (u1.search_age_min or 18) <= age <= (u1.search_age_max or 80):
        reasons.append("Yosh mos")
    if u1.intention_period == u2.intention_period:
        reasons.append("Niyat mos")
    if distance_km and distance_km <= 5:
        reasons.append("Yaqin joyda")
    return reasons or ["Tahlil qilingan"]


async def _track_view(viewer_id: int, target_id: int):
    if viewer_id == target_id:
        return
    try:
        async with async_session() as session:
            session.add(ProfileView(viewer_id=viewer_id, target_id=target_id))
            await session.commit()
    except Exception as e:
        logging.debug(f"View tracking failed: {e}")


async def send_candidate_to_user(message: types.Message, user: User, candidate: User):
    await _track_view(user.telegram_id, candidate.telegram_id)
    age = calculate_age(candidate.birth_date) or "?"
    distance = haversine(user.latitude, user.longitude, candidate.latitude, candidate.longitude)
    match_pct = get_match_percentage(user, candidate, distance)
    reasons = " • ".join(_match_reasons(user, candidate, distance))

    distance_text = ""
    if distance > 0:
        low = max(1, distance - 1)
        high = distance + 1
        distance_text = f" • 🛩 {low}-{high} km"

    verified_badge = " ✅ <i>Tasdiqlangan</i>" if candidate.is_verified else ""
    text = (
        f"<b>{candidate.full_name}</b>, {age} yosh{verified_badge}\n"
        f"📍 {candidate.region}, {candidate.district}{distance_text}\n"
        f"❤️ <b>Moslik {match_pct}%</b> • AI hisoblangan\n"
        f"<i>{reasons}</i>\n\n"
        f"<b>Bo'y/Vazn:</b> {candidate.height}sm, {candidate.weight}kg\n"
        f"<b>Ta'lim:</b> {candidate.education_level}\n"
        f"<b>Kasb:</b> {candidate.profession}\n"
        f"<b>Niyat muddati:</b> {candidate.intention_period}\n"
        f"<b>O'zi haqida:</b> {candidate.about_me}"
    )

    photos = json.loads(candidate.photos or "[]")
    photo_id = photos[0] if photos else None
    has_spoiler = candidate.gender == Gender.FEMALE
    kb = generate_candidate_kb(candidate.telegram_id)

    if photo_id:
        await message.answer_photo(
            photo=photo_id,
            caption=text,
            parse_mode="HTML",
            has_spoiler=has_spoiler,
            reply_markup=kb,
            protect_content=True,
        )
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


async def _next_candidate(user: User) -> User | None:
    target_gender = Gender.FEMALE if user.gender == Gender.MALE else Gender.MALE

    async with async_session() as session:
        req_res = await session.execute(
            select(MatchRequest.sender_id, MatchRequest.receiver_id).where(
                or_(
                    MatchRequest.sender_id == user.telegram_id,
                    MatchRequest.receiver_id == user.telegram_id,
                )
            )
        )
        excluded = {user.telegram_id}
        for r in req_res.all():
            excluded.add(r.sender_id)
            excluded.add(r.receiver_id)

        # Bloklanganlar (har ikki tomondan ham)
        block_res = await session.execute(
            select(Block.user_id, Block.target_id).where(
                or_(Block.user_id == user.telegram_id, Block.target_id == user.telegram_id)
            )
        )
        for r in block_res.all():
            excluded.add(r.user_id)
            excluded.add(r.target_id)

        candidates_res = await session.execute(
            select(User).where(
                and_(
                    User.is_active == True,  # noqa: E712
                    User.is_banned == False,  # noqa: E712
                    User.gender == target_gender,
                    User.telegram_id.notin_(excluded),
                    User.visibility != Visibility.REQUESTED_ONLY,
                )
            ).limit(50)
        )
        candidates = candidates_res.scalars().all()

    age_min = user.search_age_min or 18
    age_max = user.search_age_max or 80
    max_dist = user.search_distance_km or 50

    scored = []
    for c in candidates:
        age = calculate_age(c.birth_date)
        if not age or age < age_min or age > age_max:
            continue
        dist = haversine(user.latitude, user.longitude, c.latitude, c.longitude)
        if user.latitude and c.latitude and dist > max_dist:
            continue
        if c.visibility == Visibility.MATCHED_ONLY and c.region != user.region:
            continue
        pct = get_match_percentage(user, c, dist)
        scored.append((pct, c))

    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


@router.message(F.text.in_({"🤵‍♂️ Nomzodlar", "🤵‍♂️ Nomzodlarni ko'rish"}))
async def show_candidates(message: types.Message):
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=message.from_user.id))
        user = res.scalars().first()
    if not user:
        return await message.answer("Avval /start orqali ro'yxatdan o'ting.")
    if user.is_banned:
        return await message.answer("⚠️ Sizning profilingiz banlangan.")
    if not user.is_active:
        return await message.answer(
            "Sizning profilingiz to'xtatilgan. ⚙️ Sozlamalar orqali faollashtiring."
        )

    candidate = await _next_candidate(user)
    if not candidate:
        return await message.answer(
            "Hozircha sizning talablaringizga mos nomzodlar yo'q.\n"
            "Talablarni ⚙️ Sozlamalar → 🎯 Tanishuv talablari orqali kengaytiring."
        )
    await send_candidate_to_user(message, user, candidate)


@router.callback_query(F.data.startswith("skip_"))
async def skip_candidate(call: types.CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        pass
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=call.from_user.id))
        user = res.scalars().first()
    if not user:
        return await call.answer()
    candidate = await _next_candidate(user)
    if not candidate:
        await call.message.answer("Boshqa mos nomzod qolmadi.")
    else:
        await send_candidate_to_user(call.message, user, candidate)
    await call.answer("O'tkazib yuborildi.")


# --- Inline qidiruv ---

from aiogram.types import (  # noqa: E402
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultsButton,
    InputTextMessageContent,
)


async def _get_inline_matches(user: User, query_text: str, limit: int = 20) -> list[User]:
    target_gender = Gender.FEMALE if user.gender == Gender.MALE else Gender.MALE

    async with async_session() as session:
        req_res = await session.execute(
            select(MatchRequest.sender_id, MatchRequest.receiver_id).where(
                or_(
                    MatchRequest.sender_id == user.telegram_id,
                    MatchRequest.receiver_id == user.telegram_id,
                )
            )
        )
        excluded = {user.telegram_id}
        for r in req_res.all():
            excluded.add(r.sender_id)
            excluded.add(r.receiver_id)

        block_res = await session.execute(
            select(Block.user_id, Block.target_id).where(
                or_(Block.user_id == user.telegram_id, Block.target_id == user.telegram_id)
            )
        )
        for r in block_res.all():
            excluded.add(r.user_id)
            excluded.add(r.target_id)

        stmt = select(User).where(
            and_(
                User.is_active == True,  # noqa: E712
                User.is_banned == False,  # noqa: E712
                User.gender == target_gender,
                User.telegram_id.notin_(excluded),
                User.visibility != Visibility.REQUESTED_ONLY,
            )
        )
        if query_text:
            stmt = stmt.where(User.full_name.ilike(f"%{query_text}%"))
        stmt = stmt.limit(100)
        candidates_res = await session.execute(stmt)
        candidates = candidates_res.scalars().all()

    age_min = user.search_age_min or 18
    age_max = user.search_age_max or 80
    max_dist = user.search_distance_km or 50

    scored = []
    for c in candidates:
        age = calculate_age(c.birth_date)
        if not age or age < age_min or age > age_max:
            continue
        dist = haversine(user.latitude, user.longitude, c.latitude, c.longitude)
        if user.latitude and c.latitude and dist > max_dist:
            continue
        if c.visibility == Visibility.MATCHED_ONLY and c.region != user.region:
            continue
        pct = get_match_percentage(user, c, dist)
        scored.append((pct, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]]


@router.inline_query()
async def inline_search(query: InlineQuery):
    user_id = query.from_user.id
    me = await query.bot.me()
    bot_username = me.username

    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=user_id))
        user = res.scalars().first()

    if not user:
        return await query.answer(
            [],
            cache_time=1,
            is_personal=True,
            button=InlineQueryResultsButton(
                text="Avval ro'yxatdan o'ting",
                start_parameter="start",
            ),
        )

    if user.is_banned or not user.is_active:
        return await query.answer(
            [],
            cache_time=5,
            is_personal=True,
            button=InlineQueryResultsButton(
                text="Profilingiz faol emas — botga kirish",
                start_parameter="start",
            ),
        )

    query_text = (query.query or "").strip()
    candidates = await _get_inline_matches(user, query_text, limit=20)

    if not candidates:
        return await query.answer(
            [],
            cache_time=10,
            is_personal=True,
            button=InlineQueryResultsButton(
                text="Mos nomzod yo'q — talablarni kengaytirish",
                start_parameter="start",
            ),
        )

    results = []
    for c in candidates:
        age = calculate_age(c.birth_date) or "?"
        distance = haversine(user.latitude, user.longitude, c.latitude, c.longitude)
        pct = get_match_percentage(user, c, distance)

        verified = " ✅" if c.is_verified else ""
        title = f"{c.full_name}, {age} yosh{verified}"
        description = f"📍 {c.region or '—'} • ❤️ {pct}% mos"

        view_url = f"https://t.me/{bot_username}?start=view_{c.telegram_id}"

        results.append(
            InlineQueryResultArticle(
                id=str(c.telegram_id),
                title=title,
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "💞 <b>Juftingni Top</b>\n\n"
                        "Mos profil topildi. Faqat botda ko'ra olasiz."
                    ),
                    parse_mode="HTML",
                ),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="👁 Botda ochish", url=view_url)]
                    ]
                ),
            )
        )

    await query.answer(results, cache_time=10, is_personal=True)
