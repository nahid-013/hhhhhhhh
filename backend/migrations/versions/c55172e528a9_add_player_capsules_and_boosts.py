"""add player capsules and boosts

Revision ID: c55172e528a9
Revises: cd0b76c6d4db
Create Date: 2025-12-08 18:52:00.362101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c55172e528a9'
down_revision: Union[str, None] = 'cd0b76c6d4db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы player_capsules
    op.create_table(
        'player_capsules',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('owner_id', sa.BigInteger(), nullable=True),
        sa.Column('capsule_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('is_opened', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_opening', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('opening_started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('opening_ends_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('acquired_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.tg_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['capsule_id'], ['capsule_template.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_player_capsules_owner_id'), 'player_capsules', ['owner_id'], unique=False)

    # Создание таблицы player_boosts
    op.create_table(
        'player_boosts',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('owner_id', sa.BigInteger(), nullable=True),
        sa.Column('boost_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('acquired_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.tg_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['boost_id'], ['boost_template.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_player_boosts_owner_id'), 'player_boosts', ['owner_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_player_boosts_owner_id'), table_name='player_boosts')
    op.drop_table('player_boosts')
    op.drop_index(op.f('ix_player_capsules_owner_id'), table_name='player_capsules')
    op.drop_table('player_capsules')
