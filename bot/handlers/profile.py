import json
import logging
from datetime import datetime

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.data.regions import list_districts, list_regions
from bot.database.engine import async_session
from bot.database.models import User
from bot.keyboards.inline import (
    PROFILE_FIELDS,
    generate_photos_manage_kb,
    generate_profile_edit_kb,
)
from bot.keyboards.reply import (
    EDUCATION_OPTIONS,
    INTENTION_OPTIONS,
    MARITAL_OPTIONS,
    generate_districts_kb,
    generate_education_kb,
    generate_intention_kb,
    generate_main_menu_kb,
    generate_marital_kb,
    generate_regions_kb,
    remove_kb,
)
from bot.states.form import ProfileEditState
from bot.utils.text_filter import filter_reason

router = Router()


def _calc_age(b):
    if not b:
        return None
    today = datetime.today().date()
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))


def _profile_completion(u: User) -> int:
    fields = [
        u.full_name, u.birth_date, u.region, u.district, u.height, u.weight,
        u.marital_status, u.education_level, u.profession, u.intention_period,
        u.about_me and u.about_me != "Aytilmagan" or None,
        u.nationality, u.religion_level, u.prays,
    ]
    photos_count = len(json.loads(u.photos or "[]"))
    filled = sum(1 for f in fields if f) + (1 if photos_count >= 1 else 0) + (1 if photos_count >= 3 else 0)
    total = len(fields) + 2
    return int(filled * 100 / total)


def _format_profile(u: User) -> str:
    age = _calc_age(u.birth_date) or "—"
    gender = u.gender.value if u.gender else "—"
    verified_line = "<b>Status:</b> ✅ Tasdiqlangan\n" if u.is_verified else ""
    completion = _profile_completion(u)
    bar_filled = completion // 10
    bar = "█" * bar_filled + "░" * (10 - bar_filled)
    role_badge = " 🤝 (sovchi)" if (u.role or "user") == "sovchi" else ""
    return (
        f"👤 <b>Sizning anketangiz</b>{role_badge}\n\n"
        f"{verified_line}"
        f"<b>To'liqlik:</b> {bar} {completion}%\n\n"
        f"<b>Ism:</b> {u.full_name}, {age} yosh\n"
        f"<b>Jins:</b> {gender}\n"
        f"<b>Hudud:</b> {u.region or '—'}, {u.district or '—'}\n"
        f"<b>Bo'y/Vazn:</b> {u.height or '—'} sm, {u.weight or '—'} kg\n"
        f"<b>Nikoh holati:</b> {u.marital_status or '—'}\n"
        f"<b>Ta'lim:</b> {u.education_level or '—'}\n"
        f"<b>Kasb:</b> {u.profession or '—'}\n"
        f"<b>Niyat muddati:</b> {u.intention_period or '—'}\n"
        f"<b>Millat:</b> {u.nationality or '—'}\n"
        f"<b>Diniy holat:</b> {u.religion_level or '—'} • Namoz: {u.prays or '—'}"
        + (f" • Hijob: {u.wears_hijab}" if u.wears_hijab else "")
        + "\n"
        f"<b>O'zim haqimda:</b> {u.about_me or '—'}\n\n"
        f"<b>Holat:</b> {'Faol ✅' if u.is_active else 'To`xtatilgan ⏸'}"
    )


async def _get_user(user_id: int) -> User | None:
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=user_id))
        return res.scalars().first()


@router.message(F.text == "👤 Profilim")
async def show_profile(message: types.Message, state: FSMContext):
    await state.clear()
    user = await _get_user(message.from_user.id)
    if not user:
        return await message.answer("Avval /start orqali ro'yxatdan o'ting.")

    photos = json.loads(user.photos or "[]")
    text = _format_profile(user)
    kb = generate_profile_edit_kb()

    if photos:
        media = [types.InputMediaPhoto(media=p) for p in photos[:4]]
        try:
            await message.answer_media_group(media=media)
        except Exception as e:
            logging.warning(f"Media group failed: {e}")
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "profile_back")
async def profile_back(call: types.CallbackQuery):
    await call.message.delete()
    await call.message.answer("Asosiy menyu:", reply_markup=generate_main_menu_kb())
    await call.answer()


@router.callback_query(F.data.startswith("editfield_"))
async def edit_field(call: types.CallbackQuery, state: FSMContext):
    field = call.data.split("_", 1)[1]
    await state.update_data(edit_field=field)

    if field == "full_name":
        await call.message.answer("Yangi ismingizni yozing:", reply_markup=remove_kb())
        await state.set_state(ProfileEditState.waiting_value)
    elif field == "region_district":
        await call.message.answer(
            "Yangi viloyatni tanlang:",
            reply_markup=generate_regions_kb(list_regions()),
        )
        await state.update_data(edit_step="region")
        await state.set_state(ProfileEditState.waiting_value)
    elif field == "height_weight":
        await call.message.answer(
            "Bo'y va vaznni shu formatda yozing: <code>172 59</code>",
            parse_mode="HTML",
            reply_markup=remove_kb(),
        )
        await state.set_state(ProfileEditState.waiting_value)
    elif field == "marital_status":
        await call.message.answer("Yangi nikoh holati:", reply_markup=generate_marital_kb())
        await state.set_state(ProfileEditState.waiting_value)
    elif field == "education_level":
        await call.message.answer("Yangi ta'lim darajasi:", reply_markup=generate_education_kb())
        await state.set_state(ProfileEditState.waiting_value)
    elif field == "profession":
        await call.message.answer("Yangi kasbingiz:", reply_markup=remove_kb())
        await state.set_state(ProfileEditState.waiting_value)
    elif field == "intention_period":
        await call.message.answer("Yangi niyat muddati:", reply_markup=generate_intention_kb())
        await state.set_state(ProfileEditState.waiting_value)
    elif field == "about_me":
        await call.message.answer(
            "O'zingiz haqingizda yangi matnni yozing (max 1500):",
            reply_markup=remove_kb(),
        )
        await state.set_state(ProfileEditState.waiting_value)
    elif field == "photos":
        user = await _get_user(call.from_user.id)
        photos = json.loads(user.photos or "[]")
        await call.message.answer(
            f"Hozirgi rasmlar soni: {len(photos)}/4",
            reply_markup=generate_photos_manage_kb(len(photos)),
        )
    await call.answer()


@router.message(ProfileEditState.waiting_value, F.text)
async def receive_edit_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("edit_field")
    value = message.text.strip()

    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=message.from_user.id))
        user = res.scalars().first()
        if not user:
            await state.clear()
            return await message.answer("Foydalanuvchi topilmadi.")

        if field == "full_name":
            if len(value) < 2 or len(value) > 50:
                return await message.answer("Ism 2-50 belgi.")
            user.full_name = value
        elif field == "region_district":
            step = data.get("edit_step", "region")
            if step == "region":
                if value not in list_regions():
                    return await message.answer("Tugmadan tanlang.")
                await state.update_data(edit_step="district", new_region=value)
                return await message.answer(
                    f"<b>{value}</b> tumanini tanlang:",
                    parse_mode="HTML",
                    reply_markup=generate_districts_kb(list_districts(value)),
                )
            else:
                if value == "🔙 Viloyatni o'zgartirish":
                    await state.update_data(edit_step="region")
                    return await message.answer(
                        "Viloyatni qayta tanlang:",
                        reply_markup=generate_regions_kb(list_regions()),
                    )
                new_region = data.get("new_region")
                if value not in list_districts(new_region):
                    return await message.answer("Tumanni tugmadan tanlang.")
                user.region = new_region
                user.district = value
        elif field == "height_weight":
            parts = value.split()
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                return await message.answer("Format: <code>172 59</code>", parse_mode="HTML")
            h, w = int(parts[0]), int(parts[1])
            if not (140 <= h <= 220) or not (40 <= w <= 200):
                return await message.answer("Bo'y 140-220, vazn 40-200 oralig'ida.")
            user.height = h
            user.weight = w
        elif field == "marital_status":
            if value not in MARITAL_OPTIONS:
                return await message.answer("Tugmadan tanlang.")
            user.marital_status = value
        elif field == "education_level":
            if value not in EDUCATION_OPTIONS:
                return await message.answer("Tugmadan tanlang.")
            user.education_level = value
        elif field == "profession":
            if len(value) < 2 or len(value) > 80:
                return await message.answer("Kasb 2-80 belgi.")
            user.profession = value
        elif field == "intention_period":
            if value not in INTENTION_OPTIONS:
                return await message.answer("Tugmadan tanlang.")
            user.intention_period = value
        elif field == "about_me":
            if len(value) > 1500:
                return await message.answer("Maksimum 1500 belgi.")
            reason = filter_reason(value)
            if reason:
                return await message.answer(f"❌ {reason}\nQayta yozing.")
            user.about_me = value
        else:
            return await message.answer("Noma'lum maydon.")

        await session.commit()

    await state.clear()
    await message.answer("✅ Saqlandi.", reply_markup=generate_main_menu_kb())


@router.callback_query(F.data == "ph_back")
async def ph_back(call: types.CallbackQuery):
    await call.message.delete()
    await call.answer()


@router.callback_query(F.data == "ph_remove_last")
async def ph_remove_last(call: types.CallbackQuery):
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=call.from_user.id))
        user = res.scalars().first()
        photos = json.loads(user.photos or "[]")
        if len(photos) <= 1:
            return await call.answer("Kamida 1 ta rasm bo'lishi kerak.", show_alert=True)
        photos.pop()
        user.photos = json.dumps(photos)
        await session.commit()
    await call.message.edit_text(
        f"Rasm o'chirildi. Hozirgi: {len(photos)}/4",
        reply_markup=generate_photos_manage_kb(len(photos)),
    )
    await call.answer("O'chirildi.")


@router.callback_query(F.data == "ph_add")
async def ph_add(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Yangi rasmni yuboring:", reply_markup=remove_kb())
    await state.set_state(ProfileEditState.waiting_photo)
    await call.answer()


@router.message(ProfileEditState.waiting_photo, F.photo)
async def ph_receive(message: types.Message, state: FSMContext):
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=message.from_user.id))
        user = res.scalars().first()
        photos = json.loads(user.photos or "[]")
        if len(photos) >= 4:
            await state.clear()
            return await message.answer(
                "Maksimum 4 ta rasm.",
                reply_markup=generate_main_menu_kb(),
            )
        photos.append(message.photo[-1].file_id)
        user.photos = json.dumps(photos)
        await session.commit()
    await state.clear()
    await message.answer(
        f"✅ Qo'shildi. Jami: {len(photos)}/4",
        reply_markup=generate_main_menu_kb(),
    )


@router.message(ProfileEditState.waiting_photo)
async def ph_invalid(message: types.Message):
    await message.answer("Iltimos, rasm yuboring.")
