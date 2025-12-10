"""
Модели для слотов (Slots)
"""
from sqlalchemy import Column, Integer, BigInteger, String, Numeric, Boolean, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship

from backend.db.base_class import Base


class SlotTemplate(Base):
    """
    Шаблон слота - описывает тип слота для партии спиритов
    """
    __tablename__ = "slots_template"

    id = Column(Integer, primary_key=True, index=True)
    element_id = Column(Integer, ForeignKey("elements.id"))
    price_lumens = Column(Numeric, default=0, server_default="0")  # Цена покупки в Lumens
    sell_price_lumens = Column(Numeric, default=0, server_default="0")  # Цена продажи в Lumens
    is_starter = Column(Boolean, default=False, server_default="false")  # Стартовый слот (выдается при регистрации)
    icon_url = Column(String)
    is_available = Column(Boolean, default=True, server_default="true", index=True)  # Доступен для покупки
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    # Relationships
    element = relationship("Element", back_populates="slot_templates")
    player_slots = relationship("PlayerSlot", back_populates="template")


class PlayerSlot(Base):
    """
    Слот игрока - место для спирита в партии (до 3 активных слотов)
    """
    __tablename__ = "player_slots"

    id = Column(BigInteger, primary_key=True, index=True)
    owner_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), index=True)
    slot_template_id = Column(Integer, ForeignKey("slots_template.id"))
    element_id = Column(Integer, ForeignKey("elements.id"))  # Элемент слота (определяет какие спириты могут быть в нем)
    acquired_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))

    # Relationships
    owner = relationship("User", back_populates="slots")
    template = relationship("SlotTemplate", back_populates="player_slots")
    element = relationship("Element")
    spirit = relationship("PlayerSpirit", back_populates="slot", uselist=False)  # Один слот = один спирит
