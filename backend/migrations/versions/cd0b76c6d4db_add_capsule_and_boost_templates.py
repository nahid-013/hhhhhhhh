"""add capsule and boost templates

Revision ID: cd0b76c6d4db
Revises: 001
Create Date: 2025-12-08 18:51:20.400626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd0b76c6d4db'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы capsule_template
    op.create_table(
        'capsule_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('element_id', sa.Integer(), nullable=True),
        sa.Column('rarity_id', sa.Integer(), nullable=True),
        sa.Column('name_ru', sa.String(), nullable=True),
        sa.Column('name_en', sa.String(), nullable=True),
        sa.Column('open_time_seconds', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('price_in_ton', sa.Numeric(), nullable=True, server_default='0'),
        sa.Column('price_lumens', sa.Numeric(), nullable=True, server_default='0'),
        sa.Column('icon_url', sa.String(), nullable=True),
        sa.Column('capsule_animation_url', sa.String(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('amount', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('fast_open_cost', sa.Numeric(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['element_id'], ['elements.id'], ),
        sa.ForeignKeyConstraint(['rarity_id'], ['rarities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_capsule_template_is_available'), 'capsule_template', ['is_available'], unique=False)

    # Создание таблицы boost_template
    op.create_table(
        'boost_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('internal_name', sa.String(), nullable=True),
        sa.Column('name_ru', sa.String(), nullable=True),
        sa.Column('name_en', sa.String(), nullable=True),
        sa.Column('description_ru', sa.String(), nullable=True),
        sa.Column('description_en', sa.String(), nullable=True),
        sa.Column('price_ton', sa.Numeric(), nullable=True, server_default='0'),
        sa.Column('boost_xp', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('amount', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('icon_url', sa.String(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_boost_template_is_available'), 'boost_template', ['is_available'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_boost_template_is_available'), table_name='boost_template')
    op.drop_table('boost_template')
    op.drop_index(op.f('ix_capsule_template_is_available'), table_name='capsule_template')
    op.drop_table('capsule_template')
