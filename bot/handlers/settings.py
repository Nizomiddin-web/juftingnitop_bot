import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import delete, select

from bot.database.engine import async_session
from bot.database.models import MatchRequest, User, Visibility
from bot.keyboards.inline import (
    generate_confirm_delete_kb,
    generate_filters_kb,
    generate_settings_kb,
    generate_visibility_kb,
)
from bot.keyboards.reply import (
    DISTANCE_OPTIONS,
    generate_distance_kb,
    generate_main_menu_kb,
    remove_kb,
)
from bot.states.form import SettingsState

router = Router()


def _settings_text(u: User) -> str:
    vis = u.visibility.value if u.visibility else Visibility.MATCHED_ONLY.value
    return (
        "⚙️ <b>Sozlamalar</b>\n\n"
        f"<b>Profil ko'rinishi:</b> {vis}\n"
        f"<b>Yosh oralig'i:</b> {u.search_age_min} - {u.search_age_max}\n"
        f"<b>Qidiruv masofasi:</b> {u.search_distance_km} km\n"
        f"<b>Holat:</b> {'Faol ✅' if u.is_active else 'To`xtatilgan ⏸'}\n"
        f"<b>Bildirishnomalar:</b> {'yoqilgan' if u.notifications_on else 'o`chirilgan'}"
    )


async def _get_user(uid: int) -> User | None:
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=uid))
        return res.scalars().first()


@router.message(F.text == "⚙️ Sozlamalar")
async def show_settings(message: types.Message, state: FSMContext):
    await state.clear()
    user = await _get_user(message.from_user.id)
    if not user:
        return await message.answer("Avval /start orqali ro'yxatdan o'ting.")
    await message.answer(
        _settings_text(user),
        parse_mode="HTML",
        reply_markup=generate_settings_kb(user.is_active, user.notifications_on),
    )


@router.callback_query(F.data == "set_back")
async def back_settings(call: types.CallbackQuery):
    user = await _get_user(call.from_user.id)
    if not user:
        return await call.answer()
    try:
        await call.message.edit_text(
            _settings_text(user),
            parse_mode="HTML",
            reply_markup=generate_settings_kb(user.is_active, user.notifications_on),
        )
    except Exception:
        await call.message.answer(
            _settings_text(user),
            parse_mode="HTML",
            reply_markup=generate_settings_kb(user.is_active, user.notifications_on),
        )
    await call.answer()


@router.callback_query(F.data == "set_visibility")
async def open_visibility(call: types.CallbackQuery):
    user = await _get_user(call.from_user.id)
    current = user.visibility.name if user.visibility else "MATCHED_ONLY"
    await call.message.edit_text(
        "👁 <b>Profilingizni kim ko'rsin?</b>\n\n"
        "<b>Hammaga</b> — barcha foydalanuvchilar profilingizni ko'radi\n"
        "<b>Faqat mos kelganlarga</b> — tavsiya etiladi (jiddiy nomzodlar)\n"
        "<b>Faqat so'rov yuborganlarimga</b> — eng maxfiy variant",
        parse_mode="HTML",
        reply_markup=generate_visibility_kb(current),
    )
    await call.answer()


@router.callback_query(F.data.startswith("vis_"))
async def set_visibility(call: types.CallbackQuery):
    code = call.data.split("_", 1)[1]
    try:
        new_vis = Visibility[code]
    except KeyError:
        return await call.answer("Noma'lum tanlov.")
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=call.from_user.id))
        user = res.scalars().first()
        user.visibility = new_vis
        await session.commit()
    await call.answer("✅ Saqlandi.")
    await open_visibility(call)


@router.callback_query(F.data == "set_toggle_active")
async def toggle_active(call: types.CallbackQuery):
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=call.from_user.id))
        user = res.scalars().first()
        user.is_active = not user.is_active
        await session.commit()
        is_active = user.is_active
    await call.answer("✅ Profil faollashtirildi" if is_active else "⏸ Profil to'xtatildi")
    await back_settings(call)


@router.callback_query(F.data == "set_toggle_notif")
async def toggle_notif(call: types.CallbackQuery):
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=call.from_user.id))
        user = res.scalars().first()
        user.notifications_on = not user.notifications_on
        await session.commit()
        on = user.notifications_on
    await call.answer("🔔 Yoqildi" if on else "🔕 O'chirildi")
    await back_settings(call)


@router.callback_query(F.data == "set_delete")
async def ask_delete(call: types.CallbackQuery):
    await call.message.edit_text(
        "⚠️ <b>Profilingizni o'chirmoqchimisiz?</b>\n\n"
        "Barcha ma'lumotlaringiz va so'rovlaringiz o'chirib tashlanadi. Bu amalni bekor qilib bo'lmaydi.",
        parse_mode="HTML",
        reply_markup=generate_confirm_delete_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "del_confirm")
async def delete_profile(call: types.CallbackQuery):
    uid = call.from_user.id
    async with async_session() as session:
        await session.execute(
            delete(MatchRequest).where(
                (MatchRequest.sender_id == uid) | (MatchRequest.receiver_id == uid)
            )
        )
        await session.execute(delete(User).where(User.telegram_id == uid))
        await session.commit()
    await call.message.edit_text("✅ Profilingiz o'chirildi. /start orqali qayta ro'yxatdan o'ting.")
    await call.answer()


# --- Tanishuv talablari (filtrlar) ---


@router.callback_query(F.data == "set_filters")
async def open_filters(call: types.CallbackQuery):
    user = await _get_user(call.from_user.id)
    text = (
        "🎯 <b>Tanishuv talablari</b>\n\n"
        f"<b>Yosh oralig'i:</b> {user.search_age_min} - {user.search_age_max}\n"
        f"<b>Qidiruv masofasi:</b> {user.search_distance_km} km\n"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=generate_filters_kb())
    await call.answer()


@router.callback_query(F.data == "filter_age")
async def filter_age(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(
        "📅 <b>Eng kichik yosh</b> (18-80) raqamini kiriting:",
        parse_mode="HTML",
        reply_markup=remove_kb(),
    )
    await state.set_state(SettingsState.waiting_age_min)
    await call.answer()


@router.message(SettingsState.waiting_age_min, F.text)
async def set_age_min(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Faqat raqam.")
    age = int(message.text)
    if age < 18 or age > 80:
        return await message.answer("18-80 oralig'ida.")
    await state.update_data(age_min=age)
    await message.answer("Eng katta yosh (kiritilgan minimumdan kam emas):")
    await state.set_state(SettingsState.waiting_age_max)


@router.message(SettingsState.waiting_age_max, F.text)
async def set_age_max(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Faqat raqam.")
    data = await state.get_data()
    age_min = data.get("age_min", 18)
    age_max = int(message.text)
    if age_max < age_min or age_max > 80:
        return await message.answer(f"{age_min}-80 oralig'ida bo'lishi kerak.")

    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=message.from_user.id))
        user = res.scalars().first()
        user.search_age_min = age_min
        user.search_age_max = age_max
        await session.commit()
    await state.clear()
    await message.answer(
        f"✅ Yosh oralig'i {age_min}-{age_max} qilib saqlandi.",
        reply_markup=generate_main_menu_kb(),
    )


@router.callback_query(F.data == "filter_distance")
async def filter_distance(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("📍 Qidiruv masofasini tanlang:", reply_markup=generate_distance_kb())
    await state.set_state(SettingsState.waiting_distance)
    await call.answer()


@router.message(SettingsState.waiting_distance, F.text)
async def set_distance(message: types.Message, state: FSMContext):
    if message.text not in DISTANCE_OPTIONS:
        return await message.answer("Tugmadan tanlang.")
    km = int(message.text.split()[0])
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=message.from_user.id))
        user = res.scalars().first()
        user.search_distance_km = km
        await session.commit()
    await state.clear()
    await message.answer(
        f"✅ Qidiruv masofasi {km} km qilib saqlandi.",
        reply_markup=generate_main_menu_kb(),
    )
