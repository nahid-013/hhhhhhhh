"""
Модели для боевой системы и матчмейкинга
"""
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from backend.db.base_class import Base


class BattleSession(Base):
    """
    Сессия боя между тремя игроками

    Хранит информацию о матче, режиме игры и результаты симуляции
    """
    __tablename__ = "battle_sessions"

    id = Column(Integer, primary_key=True, index=True)
    mode = Column(String(50), nullable=False)  # flow_flight, deep_dive, rhythm_path, jump_rush, collecting_frenzy
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    result_json = Column(JSON, nullable=True)  # Полный replay боя для клиента
    created_by = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False)
    seed = Column(Integer, nullable=False)  # Seed для детерминированной генерации
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    players = relationship("BattlePlayer", back_populates="session", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class BattlePlayer(Base):
    """
    Участник боя

    Связывает игрока, его спирита и результаты боя
    """
    __tablename__ = "battle_players"

    id = Column(Integer, primary_key=True, index=True)
    battle_session_id = Column(Integer, ForeignKey("battle_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    player_id = Column(BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False, index=True)
    player_spirit_id = Column(Integer, ForeignKey("player_spirits.id", ondelete="CASCADE"), nullable=False, index=True)

    # Статистика и результаты
    stats_snapshot = Column(JSON, nullable=False)  # Статы спирита на момент боя
    score = Column(Integer, nullable=True)  # Итоговый счет в бою
    distance = Column(Float, nullable=True)  # Пройденная дистанция (для Flow Flight)
    rank = Column(Integer, nullable=True)  # Место (1, 2, 3)

    # Награды
    xp_earned = Column(Integer, nullable=True)
    lumens_earned = Column(Integer, nullable=True)
    capsule_reward_id = Column(Integer, nullable=True)  # ID полученной капсулы (если выпала)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("BattleSession", back_populates="players")
    player = relationship("User", foreign_keys=[player_id])
    spirit = relationship("PlayerSpirit", foreign_keys=[player_spirit_id])
