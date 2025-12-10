"""
Модели для бустов (Boosts)
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, TIMESTAMP, BigInteger, ForeignKey, text
from sqlalchemy.orm import relationship

from backend.db.base_class import Base


class BoostTemplate(Base):
    """
    Шаблон буста - описывает тип буста, который можно купить в магазине
    """
    __tablename__ = "boost_template"

    id = Column(Integer, primary_key=True, index=True)
    internal_name = Column(String)  # Внутреннее название для логики
    name_ru = Column(String)
    name_en = Column(String)
    description_ru = Column(String)
    description_en = Column(String)
    price_ton = Column(Numeric, default=0, server_default="0")  # Цена в TON
    boost_xp = Column(Integer, default=0, server_default="0")  # Количество XP которое даёт буст
    amount = Column(Integer, default=0, server_default="0")  # Количество в наличии (0 = безлимит)
    icon_url = Column(String)
    is_available = Column(Boolean, default=True, server_default="true", index=True)  # Доступен для покупки
    sort_order = Column(Integer)  # Порядок отображения в магазине

    # Relationships
    player_boosts = relationship("PlayerBoost", back_populates="template")


class PlayerBoost(Base):
    """
    Буст игрока - принадлежит конкретному игроку
    """
    __tablename__ = "player_boosts"

    id = Column(BigInteger, primary_key=True, index=True)
    owner_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), index=True)
    boost_id = Column(Integer, ForeignKey("boost_template.id"))
    quantity = Column(Integer, default=1, server_default="1")  # Количество таких бустов у игрока
    acquired_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    # Relationships
    owner = relationship("User", back_populates="boosts")
    template = relationship("BoostTemplate", back_populates="player_boosts")
