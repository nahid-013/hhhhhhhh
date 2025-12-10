"""
API эндпоинты для профиля пользователя
"""
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.core.security import get_current_user_id
from backend.schemas.user import UserResponse, UserUpdate
from backend.schemas.auth import WalletConnectRequest, WithdrawalRequest, WithdrawalResponse
from backend.db.repository import user as user_repo

router = APIRouter()


@router.get("/profile", response_model=dict)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Получить профиль текущего пользователя
    """
    user = await user_repo.get_user_by_tg_id(db, current_user_id)

    if not user:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "User not found"}
        }

    return {
        "ok": True,
        "data": UserResponse.model_validate(user),
        "error": None
    }


@router.patch("/profile", response_model=dict)
async def update_profile(
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Обновить профиль текущего пользователя
    """
    try:
        user = await user_repo.update_user(db, current_user_id, user_data)

        if not user:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "User not found"}
            }

        return {
            "ok": True,
            "data": UserResponse.model_validate(user),
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.post("/profile/wallet/connect", response_model=dict)
async def connect_wallet(
    request: WalletConnectRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Подключить TON кошелек к профилю
    """
    try:
        wallet = await user_repo.connect_wallet(db, current_user_id, request.address)

        return {
            "ok": True,
            "data": {
                "address": wallet.address,
                "connected_at": wallet.created_at.isoformat()
            },
            "error": None
        }
    except ValueError as e:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": str(e)}
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.post("/profile/wallet/withdraw", response_model=dict)
async def withdraw_funds(
    request: WithdrawalRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Создать запрос на вывод средств
    """
    try:
        withdrawal = await user_repo.create_withdrawal(
            db,
            current_user_id,
            Decimal(str(request.amount)),
            request.currency
        )

        return {
            "ok": True,
            "data": WithdrawalResponse.model_validate(withdrawal),
            "error": None
        }
    except ValueError as e:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INSUFFICIENT_FUNDS", "message": str(e)}
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.get("/profile/withdrawals", response_model=dict)
async def get_withdrawals(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Получить историю выводов пользователя
    """
    try:
        withdrawals = await user_repo.get_user_withdrawals(db, current_user_id)

        return {
            "ok": True,
            "data": [WithdrawalResponse.model_validate(w) for w in withdrawals],
            "error": None
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.get("/profile/referrals", response_model=dict)
async def get_referrals(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Получить список рефералов пользователя
    """
    try:
        referrals = await user_repo.get_referrals(db, current_user_id)

        return {
            "ok": True,
            "data": [UserResponse.model_validate(r) for r in referrals],
            "error": None
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.post("/profile/wallet/deposit_link", response_model=dict)
async def generate_deposit_link(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Генерация ссылки для депозита TON

    Возвращает уникальный memo для идентификации депозита
    В production можно использовать:
    - Уникальный memo на основе user_id
    - Payment links TON
    - QR коды для оплаты
    """
    try:
        user = await user_repo.get_user_by_tg_id(db, current_user_id)

        if not user:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "User not found"}
            }

        # Генерируем уникальный memo для депозита
        import hashlib
        memo = hashlib.sha256(f"deposit_{current_user_id}_{user.referral_code}".encode()).hexdigest()[:16]

        # TODO: В production здесь будет реальный treasury wallet address
        treasury_address = "EQDtFpEwcFAEcRe5mLVh2N6C0x-_hJEM7W61_JLnSF74p4q2"

        # Формируем payment link (TON format)
        payment_link = f"ton://transfer/{treasury_address}?text={memo}"

        return {
            "ok": True,
            "data": {
                "treasury_address": treasury_address,
                "memo": memo,
                "payment_link": payment_link,
                "qr_data": payment_link  # Для генерации QR кода на фронте
            },
            "error": None
        }
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.post("/profile/wallet/check_deposit", response_model=dict)
async def check_deposit(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Проверить депозиты пользователя

    В production:
    1. Запросить новые депозиты через TON indexer
    2. Фильтровать по memo пользователя
    3. Зачислить средства на баланс
    4. Сохранить в balance_logs

    Сейчас: mock для тестирования
    """
    try:
        from backend.services import ton_client

        user = await user_repo.get_user_by_tg_id(db, current_user_id)

        if not user or not user.ton_address:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NO_WALLET", "message": "No wallet connected"}
            }

        # Генерируем memo для проверки
        import hashlib
        memo = hashlib.sha256(f"deposit_{current_user_id}_{user.referral_code}".encode()).hexdigest()[:16]

        # Проверяем депозиты через TON client
        deposits = await ton_client.check_deposit(user.ton_address, memo)

        # Обработка новых депозитов
        processed = []
        for deposit in deposits:
            amount = Decimal(deposit["amount"])

            # Зачисляем на баланс
            await user_repo.add_balance(
                db,
                current_user_id,
                amount,
                "TON",
                f"deposit_{deposit['tx_hash']}"
            )

            processed.append({
                "tx_hash": deposit["tx_hash"],
                "amount": str(amount),
                "timestamp": deposit["timestamp"]
            })

        return {
            "ok": True,
            "data": {
                "deposits_count": len(processed),
                "deposits": processed
            },
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }

@router.post("/profile/donate", response_model=dict)
async def make_donation(
    amount: Decimal,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Сделать донат проекту
    """
    try:
        user = await user_repo.get_user_by_tg_id(db, current_user_id)
        if not user:
            return {"ok": False, "data": None, "error": {"code": "NOT_FOUND", "message": "User not found"}}
        
        MIN_DONATION = Decimal("1.0")
        if amount < MIN_DONATION:
            return {"ok": False, "data": None, "error": {"code": "INVALID_INPUT", "message": f"Minimum donation is {MIN_DONATION} TON"}}
        
        if user.ton_balance < amount:
            return {"ok": False, "data": None, "error": {"code": "INSUFFICIENT_FUNDS", "message": "Insufficient TON balance"}}
        
        async with db.begin():
            await user_repo.subtract_balance(db, current_user_id, amount, "TON", "donation")
            from backend.db.models.user import Donation
            donation = Donation(tg_id=current_user_id, amount=amount, currency="TON")
            db.add(donation)
            
            if user.referraled_by:
                referrer_bonus = amount * Decimal("0.1")
                await user_repo.add_balance(db, user.referraled_by, referrer_bonus, "TON", f"referral_donation_bonus")
            
            user.donate_amount = (user.donate_amount or Decimal("0")) + amount
        
        await db.commit()
        return {"ok": True, "data": {"message": "Thank you!", "amount": str(amount), "total_donated": str(user.donate_amount)}, "error": None}
    except Exception as e:
        await db.rollback()
        return {"ok": False, "data": None, "error": {"code": "DONATE_FAILED", "message": str(e)}}


@router.get("/profile/donations", response_model=dict)
async def get_donations_history(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """История донатов"""
    try:
        from backend.db.models.user import Donation
        from sqlalchemy import select
        result = await db.execute(select(Donation).where(Donation.tg_id == current_user_id).order_by(Donation.donated_at.desc()))
        donations = result.scalars().all()
        return {"ok": True, "data": [{"id": d.id, "amount": str(d.amount), "currency": d.currency, "donated_at": d.donated_at.isoformat()} for d in donations], "error": None}
    except Exception as e:
        return {"ok": False, "data": None, "error": {"code": "INTERNAL_ERROR", "message": str(e)}}
