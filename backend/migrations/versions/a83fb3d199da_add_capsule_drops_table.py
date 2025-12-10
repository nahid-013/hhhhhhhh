"""add_capsule_drops_table

Revision ID: a83fb3d199da
Revises: db96b460569c
Create Date: 2025-12-08 23:05:31.210971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a83fb3d199da'
down_revision: Union[str, None] = 'db96b460569c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Создание таблицы capsule_drops для weighted random выбора спиритов при открытии капсул
    """
    op.create_table(
        'capsule_drops',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('capsule_id', sa.Integer(), nullable=False),
        sa.Column('spirit_template_id', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['capsule_id'], ['capsule_template.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['spirit_template_id'], ['spirits_template.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Индексы для быстрого поиска
    op.create_index(
        'ix_capsule_drops_capsule_id',
        'capsule_drops',
        ['capsule_id']
    )
    op.create_index(
        'ix_capsule_drops_spirit_template_id',
        'capsule_drops',
        ['spirit_template_id']
    )


def downgrade() -> None:
    """Откат миграции"""
    op.drop_index('ix_capsule_drops_spirit_template_id')
    op.drop_index('ix_capsule_drops_capsule_id')
    op.drop_table('capsule_drops')
