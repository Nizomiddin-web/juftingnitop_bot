import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Gender(enum.Enum):
    MALE = "Erkak"
    FEMALE = "Ayol"


class Visibility(enum.Enum):
    ALL = "Hammaga"
    MATCHED_ONLY = "Faqat mos kelganlarga"
    REQUESTED_ONLY = "Faqat so'rov yuborganlarimga"


class RequestStatus(enum.Enum):
    PENDING = "Kutilmoqda"
    ACCEPTED = "Qabul qilindi"
    REJECTED = "Rad etildi"
    FINISHED = "Yakunlangan"


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(Integer, primary_key=True)
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    notifications_on = Column(Boolean, default=True)
    visibility = Column(SQLEnum(Visibility), default=Visibility.MATCHED_ONLY)
    created_at = Column(String, default=lambda: str(datetime.now()))

    full_name = Column(String(100))
    gender = Column(SQLEnum(Gender))
    birth_date = Column(Date)

    region = Column(String(100))
    district = Column(String(100))
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    height = Column(Integer)
    weight = Column(Integer)

    marital_status = Column(String(100))
    education_level = Column(String(100))
    profession = Column(String(100))

    intention_period = Column(String(50))
    about_me = Column(Text)

    search_age_min = Column(Integer, default=18)
    search_age_max = Column(Integer, default=35)
    search_distance_km = Column(Integer, default=50)
    search_education = Column(String(100), nullable=True)

    photos = Column(String, default="[]")

    # Faza 1: telefon
    phone = Column(String(20), nullable=True)

    # Faza 3: madaniy ma'lumotlar
    role = Column(String(20), default="user")  # "user" yoki "sovchi"
    nationality = Column(String(50), nullable=True)
    religion_level = Column(String(50), nullable=True)  # "Diniy" / "Diniy emas" / "Aralash"
    prays = Column(String(20), nullable=True)  # "Ha" / "Yo'q" / "Ba'zan"
    wears_hijab = Column(String(20), nullable=True)  # ayollar uchun: "Ha" / "Yo'q" / "Tayyorman"

    # Faza 2: faollik
    last_active = Column(String, default=lambda: str(datetime.now()))


class MatchRequest(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.telegram_id"))
    receiver_id = Column(Integer, ForeignKey("users.telegram_id"))
    intro_message = Column(Text, nullable=True)
    status = Column(SQLEnum(RequestStatus), default=RequestStatus.PENDING)
    created_at = Column(String, default=lambda: str(datetime.now()))

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"))
    text = Column(Text)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(String, default=lambda: str(datetime.now()))


class UserReport(Base):
    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_id = Column(Integer, ForeignKey("users.telegram_id"))
    target_id = Column(Integer, ForeignKey("users.telegram_id"))
    reason = Column(Text)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(String, default=lambda: str(datetime.now()))


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_id = Column(Integer, ForeignKey("users.telegram_id"))
    to_id = Column(Integer, ForeignKey("users.telegram_id"))
    created_at = Column(String, default=lambda: str(datetime.now()))


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"))
    target_id = Column(Integer, ForeignKey("users.telegram_id"))
    created_at = Column(String, default=lambda: str(datetime.now()))


class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"))
    target_id = Column(Integer, ForeignKey("users.telegram_id"))
    created_at = Column(String, default=lambda: str(datetime.now()))


class ProfileView(Base):
    __tablename__ = "profile_views"

    id = Column(Integer, primary_key=True, autoincrement=True)
    viewer_id = Column(Integer, ForeignKey("users.telegram_id"))
    target_id = Column(Integer, ForeignKey("users.telegram_id"))
    created_at = Column(String, default=lambda: str(datetime.now()))
