"""
Модель стихий (elements)
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.db.base_class import Base


class Element(Base):
    """Стихии в игре (fire, water, earth, air, light, dark)"""

    __tablename__ = "elements"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name_ru = Column(Text, nullable=True)
    name_en = Column(Text, nullable=True)
    icon_url = Column(Text, nullable=True)

    # Relationships
    capsule_templates = relationship("CapsuleTemplate", back_populates="element")
    slot_templates = relationship("SlotTemplate", back_populates="element")
    spirit_templates = relationship("SpiritTemplate", back_populates="element")
