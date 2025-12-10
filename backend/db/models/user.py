"""
Модель пользователей
"""
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Numeric,
    Boolean,
    ForeignKey,
    Integer,
)
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.orm import relationship
from backend.db.base_class import Base


class User(Base):
    """Модель пользователя Telegram"""

    __tablename__ = "users"

    tg_id = Column(BigInteger, primary_key=True, index=True)
    user_name = Column(Text, nullable=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    ton_address = Column(Text, nullable=True, unique=True, index=True)
    ton_balance = Column(Numeric, default=0, nullable=False)
    lumens_balance = Column(Numeric, default=1000, nullable=False)
    referral_code = Column(Text, unique=True, nullable=False, index=True)
    referraled_by = Column(BigInteger, ForeignKey("users.tg_id"), nullable=True)
    referrals_count = Column(Integer, default=0, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_admin = Column(Boolean, default=False, nullable=False)
    language = Column(Text, nullable=True)
    onboarding_step = Column(Text, nullable=True)
    donate_amount = Column(Numeric, default=0, nullable=False)
    last_active = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    wallets = relationship("Wallet", back_populates="user", cascade="all, delete-orphan")
    bans = relationship("Ban", back_populates="user", cascade="all, delete-orphan")
    donations = relationship(
        "Donation", back_populates="user", cascade="all, delete-orphan"
    )
    balance_logs = relationship(
        "BalanceLog", back_populates="user", cascade="all, delete-orphan"
    )
    withdrawals = relationship(
        "Withdrawal", back_populates="user", cascade="all, delete-orphan"
    )
    capsules = relationship(
        "PlayerCapsule", back_populates="owner", cascade="all, delete-orphan"
    )
    boosts = relationship(
        "PlayerBoost", back_populates="owner", cascade="all, delete-orphan"
    )
    slots = relationship(
        "PlayerSlot", back_populates="owner", cascade="all, delete-orphan"
    )
    spirits = relationship(
        "PlayerSpirit", back_populates="owner", cascade="all, delete-orphan"
    )
    referrer = relationship("User", remote_side=[tg_id], backref="referrals")


class Wallet(Base):
    """Модель подключенных кошельков"""

    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(BigInteger, ForeignKey("users.tg_id"), nullable=False)
    address = Column(Text, unique=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="wallets")


class Ban(Base):
    """Модель банов пользователей"""

    __tablename__ = "bans"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=True)
    banned_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="bans")


class Donation(Base):
    """Модель донатов"""

    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric, nullable=False)
    currency = Column(Text, nullable=False)
    donated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="donations")


class BalanceLog(Base):
    """Модель логов изменения баланса"""

    __tablename__ = "balance_logs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    tg_id = Column(BigInteger, ForeignKey("users.tg_id"), nullable=False)
    change = Column(Numeric, nullable=False)
    currency = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="balance_logs")


class Withdrawal(Base):
    """Модель выводов средств"""

    __tablename__ = "withdrawals"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    tg_id = Column(BigInteger, ForeignKey("users.tg_id"), nullable=False)
    amount = Column(Numeric, nullable=False)
    currency = Column(Text, nullable=False)
    status = Column(Text, default="pending", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="withdrawals")
