"""add player spirits

Revision ID: db96b460569c
Revises: b9e6889a257b
Create Date: 2025-12-08 19:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db96b460569c'
down_revision: Union[str, None] = 'b9e6889a257b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы player_spirits
    op.create_table(
        'player_spirits',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('owner_id', sa.BigInteger(), nullable=True),
        sa.Column('spirit_template_id', sa.Integer(), nullable=True),
        sa.Column('custom_name', sa.String(), nullable=True),
        sa.Column('generation', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('level', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('xp_for_next_level', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('xp', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('description_ru', sa.String(), nullable=True),
        sa.Column('description_en', sa.String(), nullable=True),
        sa.Column('base_run', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_jump', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_swim', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_dives', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_fly', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_maneuver', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_max_energy', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('energy', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('slot_id', sa.BigInteger(), nullable=True),
        sa.Column('is_minted', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('nft_id', sa.String(), nullable=True),
        sa.Column('acquired_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.tg_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['spirit_template_id'], ['spirits_template.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['slot_id'], ['player_slots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_player_spirits_owner_id'), 'player_spirits', ['owner_id'], unique=False)
    op.create_index(op.f('ix_player_spirits_is_active'), 'player_spirits', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_player_spirits_is_active'), table_name='player_spirits')
    op.drop_index(op.f('ix_player_spirits_owner_id'), table_name='player_spirits')
    op.drop_table('player_spirits')
