import json
import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import and_, select

from bot.database.engine import async_session
from bot.database.models import Gender, MatchRequest, RequestStatus, User
from bot.keyboards.inline import generate_request_action_kb
from bot.utils.text_filter import filter_reason

router = Router()


class RequestState(StatesGroup):
    waiting_for_intro = State()


@router.callback_query(F.data.startswith("sendreq_"))
async def ask_intro_message(call: types.CallbackQuery, state: FSMContext):
    target_id = int(call.data.split("_")[1])

    async with async_session() as session:
        req_res = await session.execute(
            select(MatchRequest).where(
                and_(
                    MatchRequest.sender_id == call.from_user.id,
                    MatchRequest.status.in_([RequestStatus.PENDING, RequestStatus.ACCEPTED]),
                )
            )
        )
        if req_res.scalars().first():
            return await call.answer(
                "Sizda allaqachon faol so'rov yoki tanishuv bor! Avvalgisini /yakunlash orqali tugating.",
                show_alert=True,
            )

    await state.update_data(target_id=target_id)
    await call.message.answer(
        "✍️ <b>Qisqa xabar yozing:</b>\n\n"
        "Bu xabar nomzodga sizning so'rovingiz bilan birga yetkaziladi.\n"
        "Masalan: <i>Assalomu alaykum, anketangiz menga yoqdi...</i>",
        parse_mode="HTML",
    )
    try:
        await call.message.delete()
    except Exception:
        pass
    await state.set_state(RequestState.waiting_for_intro)
    await call.answer()


@router.message(RequestState.waiting_for_intro, F.text)
async def process_send_request(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("target_id")
    intro = message.text.strip()
    if len(intro) < 3 or len(intro) > 500:
        return await message.answer("Xabar 3-500 belgi oralig'ida bo'lishi kerak.")
    reason = filter_reason(intro)
    if reason:
        return await message.answer(f"❌ {reason}\nIltimos, qayta yozing.")

    sender_id = message.from_user.id

    async with async_session() as session:
        user_res = await session.execute(select(User).filter_by(telegram_id=sender_id))
        sender_user = user_res.scalars().first()

        target_res = await session.execute(select(User).filter_by(telegram_id=target_id))
        target_user = target_res.scalars().first()

        if not target_user or not target_user.is_active:
            await state.clear()
            return await message.answer("Bu nomzod hozir mavjud emas.")

        new_req = MatchRequest(
            sender_id=sender_id,
            receiver_id=target_id,
            intro_message=intro,
            status=RequestStatus.PENDING,
        )
        session.add(new_req)
        await session.flush()
        req_id = new_req.id
        await session.commit()

    if target_user.notifications_on:
        try:
            req_text = (
                f"💌 <b>Sizga yangi tanishuv so'rovi keldi!</b>\n\n"
                f"<b>Nomzod:</b> {sender_user.full_name}\n"
                f"<b>Xabar:</b> {intro}\n\n"
                f"<i>Anketani ko'rish uchun pastdagi tugmani bosing.</i>"
            )
            await message.bot.send_message(
                chat_id=target_id,
                text=req_text,
                parse_mode="HTML",
                reply_markup=generate_request_action_kb(req_id),
            )
        except Exception as e:
            logging.error(f"Failed to notify target: {e}")

    await message.answer("✅ So'rovingiz yuborildi! Endi nomzodning javobini kutamiz.")
    await state.clear()


@router.callback_query(F.data.startswith("viewreq_"))
async def view_request_profile(call: types.CallbackQuery):
    req_id = int(call.data.split("_")[1])
    async with async_session() as session:
        res = await session.execute(select(MatchRequest).filter_by(id=req_id))
        req = res.scalars().first()
        if not req:
            return await call.answer("So'rov topilmadi.", show_alert=True)
        sres = await session.execute(select(User).filter_by(telegram_id=req.sender_id))
        sender = sres.scalars().first()

    if not sender:
        return await call.answer("Foydalanuvchi topilmadi.", show_alert=True)

    text = (
        f"<b>{sender.full_name}</b>\n"
        f"📍 {sender.region}, {sender.district}\n"
        f"<b>Bo'y/Vazn:</b> {sender.height}sm, {sender.weight}kg\n"
        f"<b>Ta'lim:</b> {sender.education_level}\n"
        f"<b>Kasb:</b> {sender.profession}\n"
        f"<b>Niyat:</b> {sender.intention_period}\n"
        f"<b>O'zi haqida:</b> {sender.about_me}"
    )
    photos = json.loads(sender.photos or "[]")
    has_spoiler = sender.gender == Gender.FEMALE
    if photos:
        await call.message.answer_photo(
            photo=photos[0],
            caption=text,
            parse_mode="HTML",
            has_spoiler=has_spoiler,
            protect_content=True,
        )
    else:
        await call.message.answer(text, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("rejectreq_"))
async def reject_request(call: types.CallbackQuery):
    req_id = int(call.data.split("_")[1])
    sender_id = None
    async with async_session() as session:
        res = await session.execute(select(MatchRequest).filter_by(id=req_id))
        req = res.scalars().first()
        if req and req.status == RequestStatus.PENDING:
            req.status = RequestStatus.REJECTED
            sender_id = req.sender_id
            await session.commit()

    if sender_id:
        try:
            await call.bot.send_message(sender_id, "❌ Sizning so'rovingiz rad etildi.")
        except Exception:
            pass
    try:
        await call.message.edit_text("So'rov rad etildi.")
    except Exception:
        await call.message.answer("So'rov rad etildi.")
    await call.answer()


@router.callback_query(F.data.startswith("acceptreq_"))
async def accept_request(call: types.CallbackQuery):
    req_id = int(call.data.split("_")[1])
    sender_id = None
    async with async_session() as session:
        res = await session.execute(select(MatchRequest).filter_by(id=req_id))
        req = res.scalars().first()
        if req and req.status == RequestStatus.PENDING:
            req.status = RequestStatus.ACCEPTED
            sender_id = req.sender_id
            await session.commit()

    if sender_id:
        try:
            await call.bot.send_message(
                sender_id,
                "✅ <b>Tabriklaymiz! So'rovingiz qabul qilindi.</b>\n\n"
                "Endi botga yozgan xabaringiz nomzodga anonim tarzda yetkaziladi.\n"
                "Suhbatni boshlang — birinchi bo'lib salom deng!\n\n"
                "Tugatish uchun: /yakunlash",
                parse_mode="HTML",
            )
        except Exception:
            pass
    try:
        await call.message.edit_text(
            "✅ Qabul qilingan. Endi botga yozgan xabaringiz nomzodga yetadi.\n"
            "Tugatish uchun: /yakunlash"
        )
    except Exception:
        pass
    await call.answer()
