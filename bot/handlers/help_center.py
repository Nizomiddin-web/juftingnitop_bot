import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.database.engine import async_session
from bot.database.models import Report, User
from bot.keyboards.inline import generate_help_back_kb, generate_help_kb
from bot.keyboards.reply import generate_main_menu_kb, remove_kb
from bot.states.form import ReportState

router = Router()


HELP_ANSWERS = {
    "h_about": (
        "🤖 <b>Juftingni Top</b> — Telegram orqali ishlovchi tanishuv boti. "
        "Sizga halol va bepul tarzda jufti haloldingizni topishga yordam beradi. "
        "Anketa to'ldirasiz, bot mos nomzodlarni ko'rsatadi."
    ),
    "h_free": (
        "💰 Ha, bot <b>butunlay bepul</b>. Hech qanday obuna, premium yoki yashirin to'lov yo'q."
    ),
    "h_request": (
        "💌 Nomzodning anketasi ostida <b>'So'rov yuborish'</b> tugmasini bosing. "
        "Qisqa xabar yozing — nomzodga sizning so'rovingiz bilan birga yetadi. "
        "U qabul qilsa, bot orqali anonim suhbat ochiladi."
    ),
    "h_concurrent": (
        "🔁 Bir vaqtda faqat <b>bitta</b> faol tanishuv jarayoni bo'lishi mumkin. "
        "Yangi so'rov yuborish uchun avvalgisini /yakunlash buyrug'i orqali tugating."
    ),
    "h_photos": (
        "🖼 Ha, ayollar rasmlari sukut bo'yicha <b>blur</b> (xiralashtirilgan) ko'rinadi. "
        "Foydalanuvchi rasm ustiga bosgandagina ochiladi. "
        "Botda screenshot himoyasi yoqilgan."
    ),
    "h_location": (
        "📍 Sizning aniq joylashuvingiz <b>hech qachon ko'rsatilmaydi</b>. "
        "Faqat taxminiy masofa (masalan: 3-5 km) yoki hudud nomi ko'rinadi."
    ),
    "h_delete": (
        "🗑 Profilingizni o'chirish uchun ⚙️ <b>Sozlamalar → Profilni o'chirish</b> tugmasini bosing. "
        "Barcha ma'lumotlar bazadan butunlay olib tashlanadi."
    ),
}


@router.message(F.text == "❓ Yordam")
async def help_root(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❓ <b>Yordam markazi</b>\n\n"
        "Quyidagi savollardan birini tanlang yoki bizga yozing:",
        parse_mode="HTML",
        reply_markup=generate_help_kb(),
    )


@router.callback_query(F.data == "h_back")
async def help_back(call: types.CallbackQuery):
    await call.message.edit_text(
        "❓ <b>Yordam markazi</b>\n\n"
        "Quyidagi savollardan birini tanlang yoki bizga yozing:",
        parse_mode="HTML",
        reply_markup=generate_help_kb(),
    )
    await call.answer()


@router.callback_query(F.data.in_(set(HELP_ANSWERS.keys())))
async def help_answer(call: types.CallbackQuery):
    text = HELP_ANSWERS[call.data]
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=generate_help_back_kb())
    await call.answer()


@router.callback_query(F.data == "h_contact")
async def help_contact(call: types.CallbackQuery):
    await call.message.edit_text(
        "🆘 <b>Qo'llab-quvvatlash</b>\n\n"
        "Savol va takliflar uchun: @juftingnitop_admin\n"
        "Email: support@juftingni.top\n\n"
        "Yoki muammoni qisqa yozing — biz oramizda hal qilamiz.",
        parse_mode="HTML",
        reply_markup=generate_help_back_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "h_report")
async def help_report(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer(
        "⚠️ Muammoni qisqa yozing (texnik xato, foydalanuvchi shikoyati va h.k.):",
        reply_markup=remove_kb(),
    )
    await state.set_state(ReportState.waiting_text)
    await call.answer()


@router.message(ReportState.waiting_text, F.text)
async def report_save(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 5:
        return await message.answer("Iltimos, kamida 5 belgili xabar yozing.")
    try:
        async with async_session() as session:
            session.add(Report(user_id=message.from_user.id, text=text))
            await session.commit()
    except Exception as e:
        logging.error(f"Report save error: {e}")
    await state.clear()
    await message.answer(
        "✅ Rahmat! Xabaringiz qabul qilindi. Tezda ko'rib chiqamiz.",
        reply_markup=generate_main_menu_kb(),
    )
