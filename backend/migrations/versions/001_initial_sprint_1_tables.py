"""initial_sprint_1_tables

Revision ID: 001
Revises:
Create Date: 2025-12-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание таблицы elements
    op.create_table(
        'elements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name_ru', sa.Text(), nullable=True),
        sa.Column('name_en', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_elements_code'), 'elements', ['code'], unique=True)
    op.create_index(op.f('ix_elements_id'), 'elements', ['id'], unique=False)

    # Создание таблицы rarities
    op.create_table(
        'rarities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name_ru', sa.Text(), nullable=True),
        sa.Column('name_en', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.Text(), nullable=True),
        sa.Column('power_factor', sa.Numeric(), nullable=False, server_default='1.0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rarities_code'), 'rarities', ['code'], unique=True)
    op.create_index(op.f('ix_rarities_id'), 'rarities', ['id'], unique=False)

    # Создание таблицы users
    op.create_table(
        'users',
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('user_name', sa.Text(), nullable=True),
        sa.Column('first_name', sa.Text(), nullable=True),
        sa.Column('last_name', sa.Text(), nullable=True),
        sa.Column('ton_address', sa.Text(), nullable=True),
        sa.Column('ton_balance', sa.Numeric(), nullable=False, server_default='0'),
        sa.Column('lumens_balance', sa.Numeric(), nullable=False, server_default='1000'),
        sa.Column('referral_code', sa.Text(), nullable=False),
        sa.Column('referraled_by', sa.BigInteger(), nullable=True),
        sa.Column('referrals_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('language', sa.Text(), nullable=True),
        sa.Column('onboarding_step', sa.Text(), nullable=True),
        sa.Column('donate_amount', sa.Numeric(), nullable=False, server_default='0'),
        sa.Column('last_active', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['referraled_by'], ['users.tg_id'], ),
        sa.PrimaryKeyConstraint('tg_id')
    )
    op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)
    op.create_index(op.f('ix_users_tg_id'), 'users', ['tg_id'], unique=False)
    op.create_index(op.f('ix_users_ton_address'), 'users', ['ton_address'], unique=True)

    # Создание таблицы bans
    op.create_table(
        'bans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('banned_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tg_id'], ['users.tg_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bans_id'), 'bans', ['id'], unique=False)

    # Создание таблицы donations
    op.create_table(
        'donations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.Column('currency', sa.Text(), nullable=False),
        sa.Column('donated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tg_id'], ['users.tg_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_donations_id'), 'donations', ['id'], unique=False)

    # Создание таблицы wallets
    op.create_table(
        'wallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tg_id'], ['users.tg_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wallets_address'), 'wallets', ['address'], unique=True)
    op.create_index(op.f('ix_wallets_id'), 'wallets', ['id'], unique=False)

    # Создание таблицы balance_logs
    op.create_table(
        'balance_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('change', sa.Numeric(), nullable=False),
        sa.Column('currency', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tg_id'], ['users.tg_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_balance_logs_id'), 'balance_logs', ['id'], unique=False)

    # Создание таблицы withdrawals
    op.create_table(
        'withdrawals',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('tg_id', sa.BigInteger(), nullable=False),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.Column('currency', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tg_id'], ['users.tg_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_withdrawals_id'), 'withdrawals', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_withdrawals_id'), table_name='withdrawals')
    op.drop_table('withdrawals')
    op.drop_index(op.f('ix_balance_logs_id'), table_name='balance_logs')
    op.drop_table('balance_logs')
    op.drop_index(op.f('ix_wallets_id'), table_name='wallets')
    op.drop_index(op.f('ix_wallets_address'), table_name='wallets')
    op.drop_table('wallets')
    op.drop_index(op.f('ix_donations_id'), table_name='donations')
    op.drop_table('donations')
    op.drop_index(op.f('ix_bans_id'), table_name='bans')
    op.drop_table('bans')
    op.drop_index(op.f('ix_users_ton_address'), table_name='users')
    op.drop_index(op.f('ix_users_tg_id'), table_name='users')
    op.drop_index(op.f('ix_users_referral_code'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_rarities_id'), table_name='rarities')
    op.drop_index(op.f('ix_rarities_code'), table_name='rarities')
    op.drop_table('rarities')
    op.drop_index(op.f('ix_elements_id'), table_name='elements')
    op.drop_index(op.f('ix_elements_code'), table_name='elements')
    op.drop_table('elements')
