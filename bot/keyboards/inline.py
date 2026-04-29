from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def generate_candidate_kb(candidate_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❤️ Yoqtirish", callback_data=f"like_{candidate_id}"),
                InlineKeyboardButton(text="💌 So'rov", callback_data=f"sendreq_{candidate_id}"),
            ],
            [
                InlineKeyboardButton(text="⭐ Saqlash", callback_data=f"save_{candidate_id}"),
                InlineKeyboardButton(text="❌ O'tkazish", callback_data=f"skip_{candidate_id}"),
            ],
            [
                InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"block_{candidate_id}"),
                InlineKeyboardButton(text="⚠️ Shikoyat", callback_data=f"report_{candidate_id}"),
            ],
        ]
    )


REPORT_REASONS = [
    ("fake", "🎭 Soxta anketa"),
    ("offensive", "🤬 Qo'pol muomala"),
    ("scam", "💸 Aldash / firibgarlik"),
    ("inappropriate", "🔞 Nomaqbul rasm yoki matn"),
    ("other", "📝 Boshqa"),
]


def generate_report_reasons_kb(target_id: int) -> InlineKeyboardMarkup:
    rows = []
    for code, label in REPORT_REASONS:
        rows.append([InlineKeyboardButton(text=label, callback_data=f"reportr_{target_id}_{code}")])
    rows.append([InlineKeyboardButton(text="◀️ Bekor", callback_data="report_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def generate_request_action_kb(request_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"acceptreq_{request_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rejectreq_{request_id}"),
            ],
            [InlineKeyboardButton(text="👁 Anketani ko'rish", callback_data=f"viewreq_{request_id}")],
        ]
    )


def generate_end_chat_kb(partner_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛑 Suhbatni yakunlash", callback_data=f"endchat_{partner_id}")]
        ]
    )


PROFILE_FIELDS = [
    ("full_name", "Ism"),
    ("region_district", "Viloyat / Tuman"),
    ("height_weight", "Bo'y va vazn"),
    ("marital_status", "Nikoh holati"),
    ("education_level", "Ta'lim darajasi"),
    ("profession", "Kasb"),
    ("intention_period", "Nikoh niyati muddati"),
    ("about_me", "O'zim haqimda"),
    ("photos", "Rasmlarim"),
]


def generate_profile_edit_kb() -> InlineKeyboardMarkup:
    rows = []
    for key, label in PROFILE_FIELDS:
        rows.append([InlineKeyboardButton(text=f"✏️ {label}", callback_data=f"editfield_{key}")])
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="profile_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def generate_settings_kb(is_active: bool, notifications_on: bool) -> InlineKeyboardMarkup:
    pause_label = "⏸ Profilni to'xtatish" if is_active else "▶️ Profilni faollashtirish"
    notif_label = "🔔 Bildirishnomalar: yoqilgan" if notifications_on else "🔕 Bildirishnomalar: o'chirilgan"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👁 Profil ko'rinishi", callback_data="set_visibility")],
            [InlineKeyboardButton(text="🎯 Tanishuv talablari", callback_data="set_filters")],
            [InlineKeyboardButton(text=pause_label, callback_data="set_toggle_active")],
            [InlineKeyboardButton(text=notif_label, callback_data="set_toggle_notif")],
            [InlineKeyboardButton(text="🗑 Profilni o'chirish", callback_data="set_delete")],
        ]
    )


def generate_visibility_kb(current: str) -> InlineKeyboardMarkup:
    options = [
        ("ALL", "Hammaga"),
        ("MATCHED_ONLY", "Faqat mos kelganlarga"),
        ("REQUESTED_ONLY", "Faqat so'rov yuborganlarimga"),
    ]
    rows = []
    for code, label in options:
        mark = "✅ " if current == code else ""
        rows.append([InlineKeyboardButton(text=f"{mark}{label}", callback_data=f"vis_{code}")])
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="set_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def generate_filters_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Yosh oralig'i", callback_data="filter_age")],
            [InlineKeyboardButton(text="📍 Qidiruv masofasi", callback_data="filter_distance")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="set_back")],
        ]
    )


def generate_confirm_delete_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data="del_confirm"),
                InlineKeyboardButton(text="❌ Bekor", callback_data="set_back"),
            ]
        ]
    )


HELP_TOPICS = [
    ("h_about", "Juftingni Top nima?"),
    ("h_free", "Ilova bepulmi?"),
    ("h_request", "So'rov qanday yuboriladi?"),
    ("h_concurrent", "Bir vaqtda nechta tanishuv bo'ladi?"),
    ("h_photos", "Rasmlarim xavfsizmi?"),
    ("h_location", "Joylashuvim ko'rinadimi?"),
    ("h_delete", "Profilimni qanday o'chirsam bo'ladi?"),
]


def generate_help_kb() -> InlineKeyboardMarkup:
    rows = []
    for code, label in HELP_TOPICS:
        rows.append([InlineKeyboardButton(text=label, callback_data=code)])
    rows.append([InlineKeyboardButton(text="🆘 Qo'llab-quvvatlash bilan bog'lanish", callback_data="h_contact")])
    rows.append([InlineKeyboardButton(text="⚠️ Muammoni xabar qilish", callback_data="h_report")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def generate_help_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="h_back")]]
    )


def generate_admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="adm_stats")],
            [InlineKeyboardButton(text="🚨 Reportlar", callback_data="adm_reports")],
            [InlineKeyboardButton(text="🔍 Foydalanuvchini topish", callback_data="adm_finduser")],
            [InlineKeyboardButton(text="📢 Hammaga xabar yuborish", callback_data="adm_broadcast")],
        ]
    )


def generate_admin_user_kb(user_id: int, is_banned: bool, is_verified: bool) -> InlineKeyboardMarkup:
    ban_label = "🔓 Banni olib tashlash" if is_banned else "🚫 Ban qilish"
    ver_label = "❌ Verifikatsiyani olib tashlash" if is_verified else "✅ Tasdiqlash"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ban_label, callback_data=f"adm_ban_{user_id}")],
            [InlineKeyboardButton(text=ver_label, callback_data=f"adm_verify_{user_id}")],
            [InlineKeyboardButton(text="🗑 Profilni o'chirish", callback_data=f"adm_del_{user_id}")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")],
        ]
    )


def generate_admin_report_kb(report_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Foydalanuvchi", callback_data=f"adm_userview_{user_id}"),
                InlineKeyboardButton(text="✅ Hal qilindi", callback_data=f"adm_resolve_{report_id}"),
            ]
        ]
    )


def generate_admin_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_back")]]
    )


def generate_broadcast_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="adm_bc_send"),
                InlineKeyboardButton(text="❌ Bekor", callback_data="adm_back"),
            ]
        ]
    )


def generate_admin_delete_confirm_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"adm_delok_{user_id}"),
                InlineKeyboardButton(text="❌ Bekor", callback_data=f"adm_userview_{user_id}"),
            ]
        ]
    )


def generate_photos_manage_kb(count: int, max_count: int = 4) -> InlineKeyboardMarkup:
    rows = []
    if count > 1:
        rows.append([InlineKeyboardButton(text="🗑 Oxirgisini o'chirish", callback_data="ph_remove_last")])
    if count < max_count:
        rows.append([InlineKeyboardButton(text="➕ Yangi rasm qo'shish", callback_data="ph_add")])
    rows.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="ph_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
