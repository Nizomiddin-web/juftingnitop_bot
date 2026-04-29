from aiogram.fsm.state import StatesGroup, State


class RegistrationState(StatesGroup):
    role = State()
    phone = State()
    full_name = State()
    gender = State()
    birth_date = State()
    location = State()
    region = State()
    district = State()
    height = State()
    weight = State()
    marital_status = State()
    education_level = State()
    profession = State()
    intention_period = State()
    nationality = State()
    religion_level = State()
    prays = State()
    wears_hijab = State()
    about_me = State()
    photos = State()


class ProfileEditState(StatesGroup):
    waiting_value = State()
    waiting_photo = State()


class SettingsState(StatesGroup):
    waiting_age_min = State()
    waiting_age_max = State()
    waiting_distance = State()


class ChatState(StatesGroup):
    active_chat = State()


class ReportState(StatesGroup):
    waiting_text = State()


class AdminState(StatesGroup):
    waiting_user_id = State()
    waiting_broadcast = State()
    waiting_broadcast_confirm = State()
