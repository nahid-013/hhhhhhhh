"""add spirits template

Revision ID: b9e6889a257b
Revises: d1f2e96ecd64
Create Date: 2025-12-08 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9e6889a257b'
down_revision: Union[str, None] = 'd1f2e96ecd64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы spirits_template
    op.create_table(
        'spirits_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('element_id', sa.Integer(), nullable=True),
        sa.Column('rarity_id', sa.Integer(), nullable=True),
        sa.Column('name_ru', sa.String(), nullable=True),
        sa.Column('name_en', sa.String(), nullable=True),
        sa.Column('generation', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('default_level', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('default_xp_for_next', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('description_ru', sa.String(), nullable=True),
        sa.Column('description_en', sa.String(), nullable=True),
        sa.Column('base_run', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_jump', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_swim', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_dives', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_fly', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_maneuver', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('base_max_energy', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('icon_url', sa.String(), nullable=True),
        sa.Column('spirit_animation_url', sa.String(), nullable=True),
        sa.Column('capsule_id', sa.Integer(), nullable=True),
        sa.Column('is_starter', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_available', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['element_id'], ['elements.id'], ),
        sa.ForeignKeyConstraint(['rarity_id'], ['rarities.id'], ),
        sa.ForeignKeyConstraint(['capsule_id'], ['capsule_template.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_spirits_template_code'), 'spirits_template', ['code'], unique=True)
    op.create_index(op.f('ix_spirits_template_is_available'), 'spirits_template', ['is_available'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_spirits_template_is_available'), table_name='spirits_template')
    op.drop_index(op.f('ix_spirits_template_code'), table_name='spirits_template')
    op.drop_table('spirits_template')
