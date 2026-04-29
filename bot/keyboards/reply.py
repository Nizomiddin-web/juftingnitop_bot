from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


MARITAL_OPTIONS = ["Birinchi marta oila quryapman", "Avval ham oila qurganman"]
EDUCATION_OPTIONS = ["O'rta", "O'rta maxsus", "Bakalavr", "Magistr", "PhD / Doktorantura"]
INTENTION_OPTIONS = ["Darhol", "3 oy ichida", "6 oy ichida", "1 yil ichida", "Aniq emas"]
DISTANCE_OPTIONS = ["5 km", "10 km", "20 km", "30 km", "50 km", "100 km"]
NATIONALITIES = ["O'zbek", "Tojik", "Qoraqalpoq", "Qozoq", "Rus", "Tatar", "Boshqa"]
RELIGION_LEVELS = ["Diniy", "Aralash", "Diniy emas"]
YES_NO_SOMETIMES = ["Ha", "Yo'q", "Ba'zan"]
HIJAB_OPTIONS = ["Ha, kiyaman", "Yo'q", "Tayyorman"]
ROLE_OPTIONS = ["👤 O'zim uchun", "🤝 Sovchi (boshqa kishi uchun)"]


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def generate_contact_location_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)],
            [KeyboardButton(text="⏭ Joylashuvsiz davom etish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_role_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=opt)] for opt in ROLE_OPTIONS],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_nationality_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=_grid(NATIONALITIES, cols=2),
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_religion_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=_grid(RELIGION_LEVELS, cols=3),
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_yes_no_sometimes_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=_grid(YES_NO_SOMETIMES, cols=3),
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_hijab_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=_grid(HIJAB_OPTIONS, cols=2),
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_gender_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Erkak"), KeyboardButton(text="Ayol")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_skip_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="O'tkazib yuborish")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _grid(items: list[str], cols: int = 2) -> list[list[KeyboardButton]]:
    rows: list[list[KeyboardButton]] = []
    row: list[KeyboardButton] = []
    for it in items:
        row.append(KeyboardButton(text=it))
        if len(row) >= cols:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


def generate_regions_kb(items: list[str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=_grid(items, cols=2),
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_districts_kb(items: list[str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=_grid(items, cols=2) + [[KeyboardButton(text="🔙 Viloyatni o'zgartirish")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_marital_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=_grid(MARITAL_OPTIONS, cols=1),
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_education_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=_grid(EDUCATION_OPTIONS, cols=2),
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_intention_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=_grid(INTENTION_OPTIONS, cols=2),
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_distance_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=_grid(DISTANCE_OPTIONS, cols=3),
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_photos_done_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Yakunlash")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def generate_main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🤵‍♂️ Nomzodlar"), KeyboardButton(text="💬 Tanishuvlar")],
            [KeyboardButton(text="💌 So'rovlar"), KeyboardButton(text="👤 Profilim")],
            [KeyboardButton(text="⭐ Saqlanganlar"), KeyboardButton(text="📊 Statistikam")],
            [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="❓ Yordam")],
        ],
        resize_keyboard=True,
    )


def generate_back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
