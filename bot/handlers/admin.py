import asyncio
import json
import logging
from datetime import datetime, timedelta

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import delete, func, select

from bot.config import is_admin
from bot.database.engine import async_session
from bot.database.models import Gender, MatchRequest, Report, RequestStatus, User
from bot.keyboards.inline import (
    generate_admin_back_kb,
    generate_admin_delete_confirm_kb,
    generate_admin_main_kb,
    generate_admin_report_kb,
    generate_admin_user_kb,
    generate_admin_users_list_kb,
    generate_broadcast_confirm_kb,
)
from bot.keyboards.reply import generate_main_menu_kb, remove_kb
from bot.states.form import AdminState

router = Router()


# --- Filtrlar (har bir handler boshida tekshiriladi) ---


def _check_admin_msg(message: types.Message) -> bool:
    return is_admin(message.from_user.id)


def _check_admin_call(call: types.CallbackQuery) -> bool:
    return is_admin(call.from_user.id)


# --- Kirish ---


@router.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext):
    if not _check_admin_msg(message):
        return
    await state.clear()
    await message.answer(
        "🛡 <b>Admin paneli</b>\n\n"
        "Komandalar: /admin · /backup\n\n"
        "Kerakli bo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=generate_admin_main_kb(),
    )


@router.message(Command("backup"))
async def admin_backup(message: types.Message):
    if not _check_admin_msg(message):
        return
    import os

    from aiogram.types import FSInputFile

    db_path = "nasib_ai.db"
    if not os.path.exists(db_path):
        return await message.answer("DB fayli topilmadi.")
    size_mb = os.path.getsize(db_path) / 1024 / 1024
    try:
        await message.answer_document(
            FSInputFile(db_path, filename=f"nasib_ai_backup_{datetime.now():%Y%m%d_%H%M}.db"),
            caption=f"💾 Backup • {size_mb:.2f} MB",
        )
    except Exception as e:
        await message.answer(f"❌ Backup xatosi: {e}")


@router.callback_query(F.data == "adm_back")
async def adm_back(call: types.CallbackQuery, state: FSMContext):
    if not _check_admin_call(call):
        return await call.answer()
    await state.clear()
    try:
        await call.message.edit_text(
            "🛡 <b>Admin paneli</b>\n\nKerakli bo'limni tanlang:",
            parse_mode="HTML",
            reply_markup=generate_admin_main_kb(),
        )
    except Exception:
        await call.message.answer(
            "🛡 <b>Admin paneli</b>",
            parse_mode="HTML",
            reply_markup=generate_admin_main_kb(),
        )
    await call.answer()


# --- Statistika ---


@router.callback_query(F.data == "adm_stats")
async def adm_stats(call: types.CallbackQuery):
    if not _check_admin_call(call):
        return await call.answer()

    async with async_session() as session:
        total = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
        active = (
            await session.execute(select(func.count()).select_from(User).where(User.is_active == True))  # noqa
        ).scalar() or 0
        banned = (
            await session.execute(select(func.count()).select_from(User).where(User.is_banned == True))  # noqa
        ).scalar() or 0
        verified = (
            await session.execute(select(func.count()).select_from(User).where(User.is_verified == True))  # noqa
        ).scalar() or 0
        males = (
            await session.execute(select(func.count()).select_from(User).where(User.gender == Gender.MALE))
        ).scalar() or 0
        females = (
            await session.execute(select(func.count()).select_from(User).where(User.gender == Gender.FEMALE))
        ).scalar() or 0

        req_total = (await session.execute(select(func.count()).select_from(MatchRequest))).scalar() or 0
        req_pending = (
            await session.execute(
                select(func.count()).select_from(MatchRequest).where(MatchRequest.status == RequestStatus.PENDING)
            )
        ).scalar() or 0
        req_accepted = (
            await session.execute(
                select(func.count()).select_from(MatchRequest).where(MatchRequest.status == RequestStatus.ACCEPTED)
            )
        ).scalar() or 0
        req_finished = (
            await session.execute(
                select(func.count()).select_from(MatchRequest).where(MatchRequest.status == RequestStatus.FINISHED)
            )
        ).scalar() or 0

        reports_open = (
            await session.execute(
                select(func.count()).select_from(Report).where(Report.is_resolved == False)  # noqa
            )
        ).scalar() or 0

        # Oxirgi 24 soatda ro'yxatdan o'tgan
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat(sep=" ")
        recent = (
            await session.execute(
                select(func.count()).select_from(User).where(User.created_at >= cutoff)
            )
        ).scalar() or 0

    text = (
        "📊 <b>Statistika</b>\n\n"
        f"<b>👥 Foydalanuvchilar:</b> {total}\n"
        f"  • Faol: {active}\n"
        f"  • Banlangan: {banned}\n"
        f"  • Tasdiqlangan: {verified}\n"
        f"  • Erkak / Ayol: {males} / {females}\n"
        f"  • Oxirgi 24 soat: +{recent}\n\n"
        f"<b>💌 So'rovlar:</b> {req_total}\n"
        f"  • Kutilmoqda: {req_pending}\n"
        f"  • Faol tanishuv: {req_accepted}\n"
        f"  • Yakunlangan: {req_finished}\n\n"
        f"<b>🚨 Ochiq reportlar:</b> {reports_open}"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=generate_admin_back_kb())
    await call.answer()


# --- Reportlar ---


@router.callback_query(F.data == "adm_reports")
async def adm_reports(call: types.CallbackQuery):
    if not _check_admin_call(call):
        return await call.answer()

    async with async_session() as session:
        res = await session.execute(
            select(Report).where(Report.is_resolved == False).order_by(Report.id.desc()).limit(10)  # noqa
        )
        reports = res.scalars().all()

    if not reports:
        return await call.message.edit_text(
            "🚨 <b>Reportlar</b>\n\nOchiq report yo'q.",
            parse_mode="HTML",
            reply_markup=generate_admin_back_kb(),
        )

    await call.message.edit_text(
        f"🚨 <b>Ochiq reportlar: {len(reports)}</b>",
        parse_mode="HTML",
        reply_markup=generate_admin_back_kb(),
    )
    for r in reports:
        text = (
            f"#{r.id} • user_id: <code>{r.user_id}</code>\n"
            f"<i>{r.created_at[:19] if r.created_at else ''}</i>\n\n"
            f"{r.text}"
        )
        await call.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=generate_admin_report_kb(r.id, r.user_id),
        )
    await call.answer()


@router.callback_query(F.data.startswith("adm_resolve_"))
async def adm_resolve(call: types.CallbackQuery):
    if not _check_admin_call(call):
        return await call.answer()
    rid = int(call.data.split("_")[2])
    async with async_session() as session:
        res = await session.execute(select(Report).filter_by(id=rid))
        rep = res.scalars().first()
        if rep:
            rep.is_resolved = True
            await session.commit()
    try:
        await call.message.edit_text(call.message.html_text + "\n\n✅ <i>Hal qilindi</i>", parse_mode="HTML")
    except Exception:
        pass
    await call.answer("✅ Hal qilindi")


# --- Foydalanuvchilar ro'yxati (qizlar / yigitlar) ---


USERS_PAGE_SIZE = 10


@router.callback_query(F.data == "adm_noop")
async def adm_noop(call: types.CallbackQuery):
    await call.answer()


@router.callback_query(F.data.regexp(r"^adm_users_[FM]_\d+$"))
async def adm_users_list(call: types.CallbackQuery):
    if not _check_admin_call(call):
        return await call.answer()

    parts = call.data.split("_")
    gender_code = parts[2]
    page = int(parts[3])
    gender = Gender.FEMALE if gender_code == "F" else Gender.MALE
    label = "👩 Qizlar" if gender == Gender.FEMALE else "👨 Yigitlar"

    async with async_session() as session:
        total = (
            await session.execute(
                select(func.count()).select_from(User).where(User.gender == gender)
            )
        ).scalar() or 0

        if total == 0:
            return await call.message.edit_text(
                f"{label}\n\nHozircha ro'yxatda hech kim yo'q.",
                parse_mode="HTML",
                reply_markup=generate_admin_back_kb(),
            )

        total_pages = (total + USERS_PAGE_SIZE - 1) // USERS_PAGE_SIZE
        page = max(0, min(page, total_pages - 1))

        res = await session.execute(
            select(User)
            .where(User.gender == gender)
            .order_by(User.created_at.desc())
            .offset(page * USERS_PAGE_SIZE)
            .limit(USERS_PAGE_SIZE)
        )
        users = res.scalars().all()

    text = (
        f"{label} <b>({total})</b> — sahifa {page+1}/{total_pages}\n\n"
        "Profilini ko'rish uchun ismni bosing."
    )
    kb = generate_admin_users_list_kb(users, page, total_pages, gender_code)
    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await call.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()


# --- Foydalanuvchini topish va boshqarish ---


@router.callback_query(F.data == "adm_finduser")
async def adm_finduser(call: types.CallbackQuery, state: FSMContext):
    if not _check_admin_call(call):
        return await call.answer()
    await call.message.answer(
        "🔍 Foydalanuvchining <b>telegram_id</b>'sini yuboring:",
        parse_mode="HTML",
        reply_markup=remove_kb(),
    )
    await state.set_state(AdminState.waiting_user_id)
    await call.answer()


@router.message(AdminState.waiting_user_id, F.text)
async def adm_userview_msg(message: types.Message, state: FSMContext):
    if not _check_admin_msg(message):
        return
    if not message.text.strip().isdigit():
        return await message.answer("Faqat raqam kiriting (telegram_id).")
    uid = int(message.text.strip())
    await state.clear()
    await _send_user_card(message, uid)


@router.callback_query(F.data.startswith("adm_userview_"))
async def adm_userview_cb(call: types.CallbackQuery):
    if not _check_admin_call(call):
        return await call.answer()
    uid = int(call.data.split("_")[2])
    await _send_user_card(call.message, uid)
    await call.answer()


async def _send_user_card(target: types.Message, user_id: int):
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=user_id))
        user = res.scalars().first()

    if not user:
        return await target.answer(f"❌ Foydalanuvchi {user_id} topilmadi.")

    age = "—"
    if user.birth_date:
        today = datetime.today().date()
        age = today.year - user.birth_date.year - (
            (today.month, today.day) < (user.birth_date.month, user.birth_date.day)
        )

    flags = []
    if user.is_verified:
        flags.append("✅ Tasdiqlangan")
    if user.is_banned:
        flags.append("🚫 Banlangan")
    if not user.is_active:
        flags.append("⏸ To'xtatilgan")
    flags_text = " • ".join(flags) if flags else "—"

    text = (
        f"👤 <b>{user.full_name or '—'}</b>, {age} yosh\n"
        f"<code>{user.telegram_id}</code>\n"
        f"Holati: {flags_text}\n\n"
        f"<b>Jins:</b> {user.gender.value if user.gender else '—'}\n"
        f"<b>Hudud:</b> {user.region or '—'}, {user.district or '—'}\n"
        f"<b>Bo'y/Vazn:</b> {user.height or '—'} sm, {user.weight or '—'} kg\n"
        f"<b>Ta'lim:</b> {user.education_level or '—'}\n"
        f"<b>Kasb:</b> {user.profession or '—'}\n"
        f"<b>Niyat:</b> {user.intention_period or '—'}\n"
        f"<b>O'zi haqida:</b> {user.about_me or '—'}"
    )
    photos = json.loads(user.photos or "[]")
    kb = generate_admin_user_kb(user.telegram_id, user.is_banned, user.is_verified)
    if photos:
        try:
            await target.answer_photo(photo=photos[0], caption=text, parse_mode="HTML", reply_markup=kb)
            return
        except Exception:
            pass
    await target.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("adm_ban_"))
async def adm_ban(call: types.CallbackQuery):
    if not _check_admin_call(call):
        return await call.answer()
    uid = int(call.data.split("_")[2])
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=uid))
        user = res.scalars().first()
        if not user:
            return await call.answer("Topilmadi.", show_alert=True)
        user.is_banned = not user.is_banned
        if user.is_banned:
            user.is_active = False
        await session.commit()
        new_state = user.is_banned

    await call.answer("🚫 Banlandi" if new_state else "🔓 Bandan chiqarildi")

    if new_state:
        try:
            await call.bot.send_message(
                uid,
                "⚠️ Sizning profilingiz qoidalarni buzgani uchun <b>banlandi</b>.\n"
                "Bog'lanish: @juftingnitop_admin",
                parse_mode="HTML",
            )
        except Exception:
            pass

    await _send_user_card(call.message, uid)


@router.callback_query(F.data.startswith("adm_verify_"))
async def adm_verify(call: types.CallbackQuery):
    if not _check_admin_call(call):
        return await call.answer()
    uid = int(call.data.split("_")[2])
    async with async_session() as session:
        res = await session.execute(select(User).filter_by(telegram_id=uid))
        user = res.scalars().first()
        if not user:
            return await call.answer("Topilmadi.", show_alert=True)
        user.is_verified = not user.is_verified
        await session.commit()
        new_state = user.is_verified

    await call.answer("✅ Tasdiqlandi" if new_state else "❌ Tasdiqlash olib tashlandi")
    if new_state:
        try:
            await call.bot.send_message(
                uid,
                "✅ Tabriklaymiz! Sizning profilingiz <b>tasdiqlandi</b>.\n"
                "Endi anketangizda 'Tasdiqlangan' belgisi ko'rinadi.",
                parse_mode="HTML",
            )
        except Exception:
            pass
    await _send_user_card(call.message, uid)


@router.callback_query(F.data.startswith("adm_del_"))
async def adm_del_ask(call: types.CallbackQuery):
    if not _check_admin_call(call):
        return await call.answer()
    uid = int(call.data.split("_")[2])
    await call.message.answer(
        f"⚠️ <b>{uid}</b> foydalanuvchini butunlay o'chirishni tasdiqlaysizmi?\n"
        "Barcha so'rovlari ham o'chiriladi.",
        parse_mode="HTML",
        reply_markup=generate_admin_delete_confirm_kb(uid),
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_delok_"))
async def adm_del_confirm(call: types.CallbackQuery):
    if not _check_admin_call(call):
        return await call.answer()
    uid = int(call.data.split("_")[2])
    async with async_session() as session:
        await session.execute(
            delete(MatchRequest).where(
                (MatchRequest.sender_id == uid) | (MatchRequest.receiver_id == uid)
            )
        )
        await session.execute(delete(User).where(User.telegram_id == uid))
        await session.commit()
    try:
        await call.message.edit_text(f"✅ Foydalanuvchi <code>{uid}</code> o'chirildi.", parse_mode="HTML")
    except Exception:
        await call.message.answer(f"✅ Foydalanuvchi {uid} o'chirildi.")
    await call.answer("O'chirildi")


# --- Broadcast ---


@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast(call: types.CallbackQuery, state: FSMContext):
    if not _check_admin_call(call):
        return await call.answer()
    await call.message.answer(
        "📢 <b>Broadcast</b>\n\n"
        "Hammaga yuboriladigan xabar matnini yuboring (HTML formatlash mumkin).\n"
        "Bekor qilish: /bekor",
        parse_mode="HTML",
        reply_markup=remove_kb(),
    )
    await state.set_state(AdminState.waiting_broadcast)
    await call.answer()


@router.message(Command("bekor"), AdminState.waiting_broadcast)
@router.message(Command("bekor"), AdminState.waiting_broadcast_confirm)
async def adm_bc_cancel(message: types.Message, state: FSMContext):
    if not _check_admin_msg(message):
        return
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=generate_main_menu_kb())


@router.message(AdminState.waiting_broadcast, F.text)
async def adm_bc_text(message: types.Message, state: FSMContext):
    if not _check_admin_msg(message):
        return
    text = message.text
    if len(text) > 3500:
        return await message.answer("Xabar juda uzun (max 3500 belgi).")
    await state.update_data(broadcast_text=text)
    await state.set_state(AdminState.waiting_broadcast_confirm)

    async with async_session() as session:
        n = (
            await session.execute(
                select(func.count()).select_from(User).where(User.is_banned == False)  # noqa
            )
        ).scalar() or 0

    await message.answer(
        f"📢 <b>Tasdiqlang</b>\n\n"
        f"Quyidagi xabar <b>{n}</b> foydalanuvchiga yuboriladi:\n\n"
        f"――――――――――\n{text}\n――――――――――",
        parse_mode="HTML",
        reply_markup=generate_broadcast_confirm_kb(),
    )


@router.callback_query(F.data == "adm_bc_send", AdminState.waiting_broadcast_confirm)
async def adm_bc_send(call: types.CallbackQuery, state: FSMContext):
    if not _check_admin_call(call):
        return await call.answer()
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()

    async with async_session() as session:
        res = await session.execute(
            select(User.telegram_id).where(User.is_banned == False)  # noqa
        )
        ids = [r[0] for r in res.all()]

    await call.message.edit_text(
        f"📤 Yuborilmoqda: 0 / {len(ids)}",
    )
    sent = 0
    failed = 0
    # Telegram limit: ~30 msg/sec global. Har 28 ta xabardan keyin 1 sec sleep.
    for i, uid in enumerate(ids, start=1):
        try:
            await call.bot.send_message(uid, text, parse_mode="HTML")
            sent += 1
        except Exception as e:
            failed += 1
            logging.debug(f"Broadcast failed for {uid}: {e}")
        if i % 28 == 0:
            await asyncio.sleep(1)
            try:
                await call.message.edit_text(f"📤 Yuborilmoqda: {i} / {len(ids)}")
            except Exception:
                pass

    await call.message.answer(
        f"✅ <b>Tugadi</b>\n\nYuborildi: {sent}\nXato: {failed}",
        parse_mode="HTML",
        reply_markup=generate_admin_main_kb(),
    )
    await call.answer()
