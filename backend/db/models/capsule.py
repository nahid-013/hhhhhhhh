"""
Модели для капсул (Capsules)
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, TIMESTAMP, BigInteger, ForeignKey, text
from sqlalchemy.orm import relationship

from backend.db.base_class import Base


class CapsuleTemplate(Base):
    """
    Шаблон капсулы - описывает тип капсулы, который можно купить в магазине
    """
    __tablename__ = "capsule_template"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    element_id = Column(Integer, ForeignKey("elements.id"))
    rarity_id = Column(Integer, ForeignKey("rarities.id"))
    name_ru = Column(String)
    name_en = Column(String)
    open_time_seconds = Column(Integer, default=0, server_default="0")  # Время открытия в секундах
    price_in_ton = Column(Numeric, default=0, server_default="0")  # Цена в TON
    price_lumens = Column(Numeric, default=0, server_default="0")  # Цена в Lumens
    icon_url = Column(String)
    capsule_animation_url = Column(String)
    is_available = Column(Boolean, default=True, server_default="true", index=True)  # Доступна для покупки
    amount = Column(Integer, default=0, server_default="0")  # Количество в наличии (0 = безлимит)
    fast_open_cost = Column(Numeric, default=0, server_default="0")  # Стоимость быстрого открытия
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    # Relationships
    element = relationship("Element", back_populates="capsule_templates")
    rarity = relationship("Rarity", back_populates="capsule_templates")
    player_capsules = relationship("PlayerCapsule", back_populates="template")
    spirit_templates = relationship("SpiritTemplate", back_populates="capsule")
    drops = relationship("CapsuleDrop", back_populates="capsule_template")


class PlayerCapsule(Base):
    """
    Капсула игрока - принадлежит конкретному игроку
    """
    __tablename__ = "player_capsules"

    id = Column(BigInteger, primary_key=True, index=True)
    owner_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), index=True)
    capsule_id = Column(Integer, ForeignKey("capsule_template.id", ondelete="SET NULL"))
    quantity = Column(Integer, default=1, server_default="1")  # Количество таких капсул у игрока
    is_opened = Column(Boolean, default=False, server_default="false")
    is_opening = Column(Boolean, default=False, server_default="false")  # В процессе открытия
    opening_started_at = Column(TIMESTAMP(timezone=True))  # Время начала открытия
    opening_ends_at = Column(TIMESTAMP(timezone=True))  # Время окончания открытия
    acquired_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    # Relationships
    owner = relationship("User", back_populates="capsules")
    template = relationship("CapsuleTemplate", back_populates="player_capsules")


class CapsuleDrop(Base):
    """
    Таблица дропов капсул - описывает какие спириты могут выпасть из капсулы и с каким весом
    """
    __tablename__ = "capsule_drops"

    id = Column(Integer, primary_key=True, index=True)
    capsule_id = Column(Integer, ForeignKey("capsule_template.id", ondelete="CASCADE"), index=True)
    spirit_template_id = Column(Integer, ForeignKey("spirits_template.id", ondelete="CASCADE"), index=True)
    weight = Column(Integer, default=1, server_default="1")  # Вес для weighted random
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    # Relationships
    capsule_template = relationship("CapsuleTemplate", back_populates="drops")
    spirit_template = relationship("SpiritTemplate", back_populates="capsule_drops")
