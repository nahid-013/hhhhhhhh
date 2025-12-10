"""add slots templates and player slots

Revision ID: d1f2e96ecd64
Revises: c55172e528a9
Create Date: 2025-12-08 18:59:39.659364

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1f2e96ecd64'
down_revision: Union[str, None] = 'c55172e528a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы slots_template
    op.create_table(
        'slots_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('element_id', sa.Integer(), nullable=True),
        sa.Column('price_lumens', sa.Numeric(), nullable=True, server_default='0'),
        sa.Column('sell_price_lumens', sa.Numeric(), nullable=True, server_default='0'),
        sa.Column('is_starter', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('icon_url', sa.String(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['element_id'], ['elements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slots_template_is_available'), 'slots_template', ['is_available'], unique=False)

    # Создание таблицы player_slots
    op.create_table(
        'player_slots',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('owner_id', sa.BigInteger(), nullable=True),
        sa.Column('slot_template_id', sa.Integer(), nullable=True),
        sa.Column('element_id', sa.Integer(), nullable=True),
        sa.Column('acquired_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.tg_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['slot_template_id'], ['slots_template.id'], ),
        sa.ForeignKeyConstraint(['element_id'], ['elements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_player_slots_owner_id'), 'player_slots', ['owner_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_player_slots_owner_id'), table_name='player_slots')
    op.drop_table('player_slots')
    op.drop_index(op.f('ix_slots_template_is_available'), table_name='slots_template')
    op.drop_table('slots_template')
