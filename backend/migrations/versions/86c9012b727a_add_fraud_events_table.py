"""add_fraud_events_table

Revision ID: 86c9012b727a
Revises: a83fb3d199da
Create Date: 2025-12-08 23:23:28.795868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86c9012b727a'
down_revision: Union[str, None] = 'a83fb3d199da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'fraud_events',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('severity', sa.String(), server_default='low', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tg_id'], ['users.tg_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fraud_events_tg_id', 'fraud_events', ['tg_id'])
    op.create_index('ix_fraud_events_event_type', 'fraud_events', ['event_type'])
    op.create_index('ix_fraud_events_created_at', 'fraud_events', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_fraud_events_created_at', table_name='fraud_events')
    op.drop_index('ix_fraud_events_event_type', table_name='fraud_events')
    op.drop_index('ix_fraud_events_tg_id', table_name='fraud_events')
    op.drop_table('fraud_events')
