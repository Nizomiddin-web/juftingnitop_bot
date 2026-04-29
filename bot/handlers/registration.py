import json
import logging
from datetime import datetime

from aiogram import F, Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.data.regions import list_districts, list_regions
from bot.database.engine import async_session
from bot.database.models import Gender, User
from bot.keyboards.reply import (
    EDUCATION_OPTIONS,
    HIJAB_OPTIONS,
    INTENTION_OPTIONS,
    MARITAL_OPTIONS,
    NATIONALITIES,
    RELIGION_LEVELS,
    ROLE_OPTIONS,
    YES_NO_SOMETIMES,
    generate_contact_location_kb,
    generate_districts_kb,
    generate_education_kb,
    generate_gender_kb,
    generate_hijab_kb,
    generate_intention_kb,
    generate_main_menu_kb,
    generate_marital_kb,
    generate_nationality_kb,
    generate_phone_kb,
    generate_photos_done_kb,
    generate_regions_kb,
    generate_religion_kb,
    generate_role_kb,
    generate_skip_kb,
    generate_yes_no_sometimes_kb,
    remove_kb,
)
from bot.states.form import RegistrationState
from bot.utils.text_filter import filter_reason

router = Router()

MAX_PHOTOS = 4


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).filter_by(telegram_id=user_id))
        user = result.scalars().first()

    if user:
        await message.answer(
            "Siz allaqachon ro'yxatdan o'tgansiz! Asosiy menyu:",
            reply_markup=generate_main_menu_kb(),
        )
        return

    await message.answer(
        "Assalomu alaykum! <b>Juftingni Top</b> tanishuv botiga xush kelibsiz.\n\n"
        "Botimiz <b>butunlay bepul</b> va sizga halol tanishuv imkonini beradi.\n\n"
        "Anketa kim uchun?",
        parse_mode="HTML",
        reply_markup=generate_role_kb(),
    )
    await state.set_state(RegistrationState.role)


@router.message(RegistrationState.role, F.text)
async def process_role(message: types.Message, state: FSMContext):
    if message.text not in ROLE_OPTIONS:
        return await message.answer("Iltimos, tugmadan tanlang.")
    is_sovchi = message.text.startswith("🤝")
    await state.update_data(role="sovchi" if is_sovchi else "user")
    await message.answer(
        "📱 Raqamingizni tasdiqlang. <b>'Raqamni yuborish'</b> tugmasini bosing.\n"
        "Bu raqam boshqalarga ko'rsatilmaydi — faqat verifikatsiya uchun.",
        parse_mode="HTML",
        reply_markup=generate_phone_kb(),
    )
    await state.set_state(RegistrationState.phone)


@router.message(RegistrationState.phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    if message.contact.user_id != message.from_user.id:
        return await message.answer(
            "❌ Iltimos, o'z raqamingizni yuboring.",
            reply_markup=generate_phone_kb(),
        )
    await state.update_data(phone=message.contact.phone_number)
    data = await state.get_data()
    if data.get("role") == "sovchi":
        await message.answer(
            "Sovchi sifatida ro'yxatdan o'tyapsiz. Endi qaysi shaxs uchun anketa to'ldirayotganingizni kiriting.\n"
            "Uning ismi:",
            reply_markup=remove_kb(),
        )
    else:
        await message.answer("Endi ismingizni kiriting:", reply_markup=remove_kb())
    await state.set_state(RegistrationState.full_name)


@router.message(RegistrationState.phone)
async def phone_invalid(message: types.Message):
    await message.answer(
        "Iltimos, '📱 Raqamni yuborish' tugmasini bosing.",
        reply_markup=generate_phone_kb(),
    )


@router.message(RegistrationState.full_name, F.text)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        return await message.answer("Ism 2 dan 50 belgigacha bo'lishi kerak. Qayta kiriting:")
    await state.update_data(full_name=name)
    await message.answer("Jinsingizni tanlang:", reply_markup=generate_gender_kb())
    await state.set_state(RegistrationState.gender)


@router.message(RegistrationState.gender, F.text)
async def process_gender(message: types.Message, state: FSMContext):
    if message.text not in ["Erkak", "Ayol"]:
        return await message.answer("Iltimos, tugmalardan birini tanlang.")
    await state.update_data(gender=Gender.MALE if message.text == "Erkak" else Gender.FEMALE)
    await message.answer(
        "Tug'ilgan sanangizni kiriting (DD.MM.YYYY format).\nMasalan: 02.12.1999",
        reply_markup=remove_kb(),
    )
    await state.set_state(RegistrationState.birth_date)


@router.message(RegistrationState.birth_date, F.text)
async def process_birth_date(message: types.Message, state: FSMContext):
    try:
        b_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        return await message.answer("Xato format! Yana bir bor kiriting (DD.MM.YYYY).")

    today = datetime.today().date()
    age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
    if age < 18 or age > 80:
        return await message.answer("Yoshingiz 18 dan 80 gacha bo'lishi kerak. Qayta kiriting:")

    await state.update_data(birth_date=b_date)
    await message.answer(
        "Yashash viloyatingizni tanlang:",
        reply_markup=generate_regions_kb(list_regions()),
    )
    await state.set_state(RegistrationState.region)


@router.message(RegistrationState.region, F.text)
async def process_region(message: types.Message, state: FSMContext):
    region = message.text.strip()
    if region not in list_regions():
        return await message.answer("Iltimos, ro'yxatdan tugma orqali tanlang.")
    await state.update_data(region=region)
    await message.answer(
        f"<b>{region}</b> uchun tumaningizni tanlang:",
        parse_mode="HTML",
        reply_markup=generate_districts_kb(list_districts(region)),
    )
    await state.set_state(RegistrationState.district)


@router.message(RegistrationState.district, F.text)
async def process_district(message: types.Message, state: FSMContext):
    if message.text == "🔙 Viloyatni o'zgartirish":
        await message.answer(
            "Viloyatni qayta tanlang:",
            reply_markup=generate_regions_kb(list_regions()),
        )
        await state.set_state(RegistrationState.region)
        return

    data = await state.get_data()
    region = data.get("region")
    if message.text not in list_districts(region):
        return await message.answer("Iltimos, tumanni tugmadan tanlang.")
    await state.update_data(district=message.text.strip())
    await message.answer(
        "Aniq masofa hisoblanishi uchun joylashuvni yuboring (ixtiyoriy):",
        reply_markup=generate_contact_location_kb(),
    )
    await state.set_state(RegistrationState.location)


@router.message(RegistrationState.location, F.location)
async def process_location(message: types.Message, state: FSMContext):
    loc = message.location
    await state.update_data(latitude=loc.latitude, longitude=loc.longitude)
    await _ask_height(message, state)


@router.message(RegistrationState.location, F.text == "⏭ Joylashuvsiz davom etish")
async def process_location_skip(message: types.Message, state: FSMContext):
    await state.update_data(latitude=None, longitude=None)
    await _ask_height(message, state)


@router.message(RegistrationState.location)
async def process_location_invalid(message: types.Message, state: FSMContext):
    await message.answer(
        "Iltimos, '📍 Joylashuvni yuborish' tugmasini bosing yoki o'tkazib yuboring.",
        reply_markup=generate_contact_location_kb(),
    )


async def _ask_height(message: types.Message, state: FSMContext):
    await message.answer("Bo'yingiz necha sm? (140-220 oralig'ida)", reply_markup=remove_kb())
    await state.set_state(RegistrationState.height)


@router.message(RegistrationState.height, F.text)
async def process_height(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Faqat raqam kiriting.")
    h = int(message.text)
    if h < 140 or h > 220:
        return await message.answer("Bo'y 140-220 sm oralig'ida bo'lishi kerak.")
    await state.update_data(height=h)
    await message.answer("Vazningiz necha kg? (40-200)")
    await state.set_state(RegistrationState.weight)


@router.message(RegistrationState.weight, F.text)
async def process_weight(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Faqat raqam kiriting.")
    w = int(message.text)
    if w < 40 or w > 200:
        return await message.answer("Vazn 40-200 kg oralig'ida bo'lishi kerak.")
    await state.update_data(weight=w)
    await message.answer("Nikoh holatingizni tanlang:", reply_markup=generate_marital_kb())
    await state.set_state(RegistrationState.marital_status)


@router.message(RegistrationState.marital_status, F.text)
async def process_marital(message: types.Message, state: FSMContext):
    if message.text not in MARITAL_OPTIONS:
        return await message.answer("Iltimos, tugmalardan tanlang.")
    await state.update_data(marital_status=message.text)
    await message.answer("Ta'lim darajangizni tanlang:", reply_markup=generate_education_kb())
    await state.set_state(RegistrationState.education_level)


@router.message(RegistrationState.education_level, F.text)
async def process_education(message: types.Message, state: FSMContext):
    if message.text not in EDUCATION_OPTIONS:
        return await message.answer("Iltimos, tugmalardan tanlang.")
    await state.update_data(education_level=message.text)
    await message.answer(
        "Kasbingizni qisqa yozing (masalan: Odoo dasturchisi).",
        reply_markup=remove_kb(),
    )
    await state.set_state(RegistrationState.profession)


@router.message(RegistrationState.profession, F.text)
async def process_profession(message: types.Message, state: FSMContext):
    p = message.text.strip()
    if len(p) < 2 or len(p) > 80:
        return await message.answer("Kasb 2 dan 80 belgigacha. Qayta kiriting:")
    await state.update_data(profession=p)
    await message.answer("Nikoh niyati muddatini tanlang:", reply_markup=generate_intention_kb())
    await state.set_state(RegistrationState.intention_period)


@router.message(RegistrationState.intention_period, F.text)
async def process_intention(message: types.Message, state: FSMContext):
    if message.text not in INTENTION_OPTIONS:
        return await message.answer("Iltimos, tugmalardan tanlang.")
    await state.update_data(intention_period=message.text)
    await message.answer("Millatingizni tanlang:", reply_markup=generate_nationality_kb())
    await state.set_state(RegistrationState.nationality)


@router.message(RegistrationState.nationality, F.text)
async def process_nationality(message: types.Message, state: FSMContext):
    if message.text not in NATIONALITIES:
        return await message.answer("Iltimos, tugmadan tanlang.")
    await state.update_data(nationality=message.text)
    await message.answer(
        "Diniy holatingizni tanlang:",
        reply_markup=generate_religion_kb(),
    )
    await state.set_state(RegistrationState.religion_level)


@router.message(RegistrationState.religion_level, F.text)
async def process_religion(message: types.Message, state: FSMContext):
    if message.text not in RELIGION_LEVELS:
        return await message.answer("Iltimos, tugmadan tanlang.")
    await state.update_data(religion_level=message.text)
    await message.answer("Namoz o'qiysizmi?", reply_markup=generate_yes_no_sometimes_kb())
    await state.set_state(RegistrationState.prays)


@router.message(RegistrationState.prays, F.text)
async def process_prays(message: types.Message, state: FSMContext):
    if message.text not in YES_NO_SOMETIMES:
        return await message.answer("Iltimos, tugmadan tanlang.")
    await state.update_data(prays=message.text)

    data = await state.get_data()
    gender = data.get("gender")
    from bot.database.models import Gender as G
    if gender == G.FEMALE:
        await message.answer("Hijob masalasi:", reply_markup=generate_hijab_kb())
        await state.set_state(RegistrationState.wears_hijab)
    else:
        await _ask_about(message, state)


@router.message(RegistrationState.wears_hijab, F.text)
async def process_hijab(message: types.Message, state: FSMContext):
    if message.text not in HIJAB_OPTIONS:
        return await message.answer("Iltimos, tugmadan tanlang.")
    await state.update_data(wears_hijab=message.text)
    await _ask_about(message, state)


async def _ask_about(message: types.Message, state: FSMContext):
    await message.answer(
        "O'zingiz haqingizda qisqa yozing (xarakter, qiziqishlar, qadriyatlar).\n"
        "Maksimal 1500 belgi.",
        reply_markup=generate_skip_kb(),
    )
    await state.set_state(RegistrationState.about_me)


@router.message(RegistrationState.about_me, F.text)
async def process_about(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "O'tkazib yuborish":
        text = "Aytilmagan"
    if len(text) > 1500:
        return await message.answer("1500 belgidan kam yozing.")
    if text != "Aytilmagan":
        reason = filter_reason(text)
        if reason:
            return await message.answer(f"❌ {reason}\nQayta yozing.")
    await state.update_data(about_me=text)
    await state.update_data(photos=[])
    await message.answer(
        f"Endi rasmlaringizni yuboring (1 dan {MAX_PHOTOS} tagacha).\n"
        f"Birinchi rasm <b>asosiy</b> bo'ladi.\n"
        f"Tayyor bo'lsangiz '✅ Yakunlash' tugmasini bosing.",
        parse_mode="HTML",
        reply_markup=generate_photos_done_kb(),
    )
    await state.set_state(RegistrationState.photos)


@router.message(RegistrationState.photos, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos: list[str] = list(data.get("photos") or [])
    if len(photos) >= MAX_PHOTOS:
        return await message.answer(
            f"Maksimum {MAX_PHOTOS} ta rasm. '✅ Yakunlash' tugmasini bosing."
        )
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    if len(photos) < MAX_PHOTOS:
        await message.answer(
            f"✅ Qabul qilindi. Jami: {len(photos)}/{MAX_PHOTOS}.\n"
            "Yana yuborishingiz yoki '✅ Yakunlash' tugmasini bosishingiz mumkin."
        )
    else:
        await message.answer(
            f"✅ {MAX_PHOTOS} ta rasm to'plandi. '✅ Yakunlash' tugmasini bosing."
        )


@router.message(RegistrationState.photos, F.text == "✅ Yakunlash")
async def finish_registration(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = list(data.get("photos") or [])
    if not photos:
        return await message.answer("Iltimos, kamida bitta rasm yuboring.")

    try:
        async with async_session() as session:
            new_user = User(
                telegram_id=message.from_user.id,
                full_name=data.get("full_name"),
                gender=data.get("gender"),
                birth_date=data.get("birth_date"),
                region=data.get("region"),
                district=data.get("district"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                height=data.get("height"),
                weight=data.get("weight"),
                marital_status=data.get("marital_status"),
                education_level=data.get("education_level"),
                profession=data.get("profession"),
                intention_period=data.get("intention_period"),
                about_me=data.get("about_me") or "Aytilmagan",
                photos=json.dumps(photos),
                phone=data.get("phone"),
                role=data.get("role", "user"),
                nationality=data.get("nationality"),
                religion_level=data.get("religion_level"),
                prays=data.get("prays"),
                wears_hijab=data.get("wears_hijab"),
            )
            session.add(new_user)
            await session.commit()
    except Exception as e:
        logging.exception(f"Registration save error: {e!r}")
        await message.answer("Bazada xatolik yuz berdi. /start ni qaytadan bosing.")
        await state.clear()
        return

    await message.answer(
        "🎉 Tabriklaymiz! Profilingiz tayyor.\n"
        "Endi nomzodlarni ko'rishingiz va so'rov yuborishingiz mumkin.",
        reply_markup=generate_main_menu_kb(),
    )
    await state.clear()


@router.message(RegistrationState.photos)
async def photos_invalid(message: types.Message):
    await message.answer(
        "Iltimos, rasm yuboring yoki '✅ Yakunlash' tugmasini bosing.",
        reply_markup=generate_photos_done_kb(),
    )
