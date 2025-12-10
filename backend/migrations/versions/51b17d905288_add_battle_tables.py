"""add_battle_tables

Revision ID: 51b17d905288
Revises: bc1e543c9181
Create Date: 2025-12-10 00:20:46.128264

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51b17d905288'
down_revision: Union[str, None] = 'bc1e543c9181'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создать таблицу battle_sessions
    op.create_table(
        'battle_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(50), nullable=False, comment='Режим игры: flow_flight, deep_dive, rhythm_path, jump_rush, collecting_frenzy'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('result_json', sa.JSON(), nullable=True, comment='Детальный replay боя'),
        sa.Column('created_by', sa.BigInteger(), nullable=False, comment='Telegram ID игрока, создавшего бой'),
        sa.Column('seed', sa.Integer(), nullable=False, comment='Seed для детерминированной симуляции'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.tg_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Создать индексы для battle_sessions
    op.create_index('ix_battle_sessions_created_by', 'battle_sessions', ['created_by'])
    op.create_index('ix_battle_sessions_mode', 'battle_sessions', ['mode'])
    op.create_index('ix_battle_sessions_finished_at', 'battle_sessions', ['finished_at'])

    # Создать таблицу battle_players
    op.create_table(
        'battle_players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('battle_session_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.BigInteger(), nullable=False, comment='Telegram ID игрока'),
        sa.Column('player_spirit_id', sa.Integer(), nullable=False, comment='ID спирита, участвующего в бою'),
        sa.Column('stats_snapshot', sa.JSON(), nullable=False, comment='Снапшот статов спирита на момент боя'),
        sa.Column('score', sa.Integer(), nullable=True, comment='Набранные очки в бою'),
        sa.Column('distance', sa.Float(), nullable=True, comment='Пройденная дистанция (для Flow Flight)'),
        sa.Column('rank', sa.Integer(), nullable=True, comment='Место в бою: 1, 2, 3'),
        sa.Column('xp_earned', sa.Integer(), nullable=True, comment='Заработанный XP'),
        sa.Column('lumens_earned', sa.Integer(), nullable=True, comment='Заработанные Lumens'),
        sa.Column('capsule_reward_id', sa.Integer(), nullable=True, comment='ID полученной капсулы (если выпала)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['battle_session_id'], ['battle_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player_id'], ['users.tg_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player_spirit_id'], ['player_spirits.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Создать индексы для battle_players
    op.create_index('ix_battle_players_battle_session_id', 'battle_players', ['battle_session_id'])
    op.create_index('ix_battle_players_player_id', 'battle_players', ['player_id'])
    op.create_index('ix_battle_players_player_spirit_id', 'battle_players', ['player_spirit_id'])


def downgrade() -> None:
    # Удалить таблицы в обратном порядке
    op.drop_index('ix_battle_players_player_spirit_id', table_name='battle_players')
    op.drop_index('ix_battle_players_player_id', table_name='battle_players')
    op.drop_index('ix_battle_players_battle_session_id', table_name='battle_players')
    op.drop_table('battle_players')

    op.drop_index('ix_battle_sessions_finished_at', table_name='battle_sessions')
    op.drop_index('ix_battle_sessions_mode', table_name='battle_sessions')
    op.drop_index('ix_battle_sessions_created_by', table_name='battle_sessions')
    op.drop_table('battle_sessions')
