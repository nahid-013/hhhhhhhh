"""
Celery задачи для экономической системы
"""
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from workers.celery_app import celery_app
from backend.db.session import async_session_maker
from backend.db.models.user import Withdrawal, User
from backend.services import ton_client


MIN_WITHDRAWAL_AMOUNT = Decimal("10.0")  # Минимум 10 TON
WITHDRAWAL_DELAY_NEW_ACCOUNTS = 24  # 24 часа для новых аккаунтов
WITHDRAWAL_DELAY_FLAGGED = 72  # 72 часа для подозрительных


async def _process_withdrawals_async():
    """
    Async обработка withdrawals
    """
    async with async_session_maker() as db:
        try:
            # Получаем все pending withdrawals
            result = await db.execute(
                select(Withdrawal)
                .where(Withdrawal.status == "pending")
                .order_by(Withdrawal.created_at)
            )
            pending_withdrawals = result.scalars().all()

            if not pending_withdrawals:
                return {"processed": 0, "message": "No pending withdrawals"}

            processed_count = 0
            rejected_count = 0
            delayed_count = 0

            for withdrawal in pending_withdrawals:
                # Получаем пользователя
                user_result = await db.execute(
                    select(User).where(User.tg_id == withdrawal.tg_id)
                )
                user = user_result.scalar_one_or_none()

                if not user:
                    # Отклоняем если пользователь не найден
                    withdrawal.status = "rejected"
                    withdrawal.completed_at = datetime.utcnow()
                    rejected_count += 1
                    continue

                # Проверка минимальной суммы
                if withdrawal.amount < MIN_WITHDRAWAL_AMOUNT:
                    withdrawal.status = "rejected"
                    withdrawal.completed_at = datetime.utcnow()
                    rejected_count += 1
                    continue

                # Проверка наличия кошелька
                if not user.ton_address:
                    withdrawal.status = "rejected"
                    withdrawal.completed_at = datetime.utcnow()
                    rejected_count += 1
                    continue

                # Проверка delay для новых аккаунтов
                account_age = (datetime.utcnow() - user.created_at).total_seconds() / 3600
                required_delay = WITHDRAWAL_DELAY_NEW_ACCOUNTS

                # TODO: Добавить проверку is_flagged когда будет anti-fraud
                # if user.is_flagged:
                #     required_delay = WITHDRAWAL_DELAY_FLAGGED

                withdrawal_age = (datetime.utcnow() - withdrawal.created_at).total_seconds() / 3600

                if account_age < 24 and withdrawal_age < required_delay:
                    # Еще рано для вывода
                    delayed_count += 1
                    continue

                # Обновляем статус на processing
                withdrawal.status = "processing"
                await db.flush()

                try:
                    # Отправляем TON через TON Service
                    tx_result = await ton_client.send_ton(
                        to_address=user.ton_address,
                        amount=withdrawal.amount,
                        memo=f"withdrawal_{withdrawal.id}"
                    )

                    # Успешно отправлено
                    withdrawal.status = "completed"
                    withdrawal.completed_at = datetime.utcnow()
                    # Можно сохранить tx_hash в отдельное поле если нужно
                    processed_count += 1

                except Exception as e:
                    # Ошибка отправки - вернуть в pending или rejected
                    withdrawal.status = "rejected"
                    withdrawal.completed_at = datetime.utcnow()
                    rejected_count += 1
                    print(f"Withdrawal {withdrawal.id} failed: {str(e)}")

            await db.commit()

            return {
                "processed": processed_count,
                "rejected": rejected_count,
                "delayed": delayed_count,
                "total": len(pending_withdrawals)
            }

        except Exception as e:
            await db.rollback()
            print(f"Error processing withdrawals: {str(e)}")
            return {"error": str(e)}


@celery_app.task(name="workers.tasks.economy.process_withdrawals")
def process_withdrawals():
    """
    Batch обработка pending выводов TON

    Запускается периодически (каждые 10-30 минут)

    Логика:
    1. Получить все pending withdrawals из БД
    2. Проверить delay для новых/flagged аккаунтов (24-72ч)
    3. Вызов TON Service для отправки TON
    4. Обновить status на processing/completed/rejected
    5. Добавить записи в balance_logs

    Returns:
        dict: Статистика обработки
    """
    return asyncio.run(_process_withdrawals_async())


@celery_app.task(name="workers.tasks.economy.apply_referral_rewards")
def apply_referral_rewards(user_id: int):
    """
    Применяет реферальные награды (milestone bonuses)
    TODO: Реализовать в Sprint 1

    Args:
        user_id: ID пользователя (referrer)
    """
    # TODO:
    # 1. Проверить количество рефералов
    # 2. Если кратно 5 -> начислить +0.5 TON
    # 3. Обновить баланс в БД
    # 4. Добавить запись в balance_logs
    print(f"apply_referral_rewards task for user_id={user_id} - TODO: implement")
    return {"status": "ok", "user_id": user_id}
