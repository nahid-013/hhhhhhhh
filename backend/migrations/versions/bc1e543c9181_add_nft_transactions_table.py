"""add_nft_transactions_table

Revision ID: bc1e543c9181
Revises: 86c9012b727a
Create Date: 2025-12-08 23:39:06.793098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc1e543c9181'
down_revision: Union[str, None] = '86c9012b727a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'nft_transactions',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('player_spirit_id', sa.BigInteger(), nullable=False),
        sa.Column('operation', sa.String(), nullable=False),  # mint, burn, transfer
        sa.Column('tx_hash', sa.String(), nullable=True),  # Blockchain transaction hash
        sa.Column('status', sa.String(), server_default='pending', nullable=False),  # pending, processing, completed, failed
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['player_spirit_id'], ['player_spirits.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_nft_transactions_player_spirit_id', 'nft_transactions', ['player_spirit_id'])
    op.create_index('ix_nft_transactions_operation', 'nft_transactions', ['operation'])
    op.create_index('ix_nft_transactions_status', 'nft_transactions', ['status'])
    op.create_index('ix_nft_transactions_created_at', 'nft_transactions', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_nft_transactions_created_at', table_name='nft_transactions')
    op.drop_index('ix_nft_transactions_status', table_name='nft_transactions')
    op.drop_index('ix_nft_transactions_operation', table_name='nft_transactions')
    op.drop_index('ix_nft_transactions_player_spirit_id', table_name='nft_transactions')
    op.drop_table('nft_transactions')
