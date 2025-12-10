"""
API эндпоинты для капсул
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List, Optional

from backend.db.session import get_db
from backend.schemas.capsule import (
    CapsuleTemplateResponse,
    PlayerCapsuleResponse,
    CapsuleBuyRequest,
    CapsuleBuyResponse,
    CapsuleOpenRequest,
    CapsuleFastOpenRequest,
)
from backend.db.repository import capsule as capsule_repo
from backend.db.repository import user as user_repo
from backend.core.security import get_current_user_id

router = APIRouter()


@router.get("/capsules/shop", response_model=dict)
async def get_capsule_shop(
    element_id: Optional[int] = None,
    rarity_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Получение магазина капсул (группировка по element/rarity)
    """
    templates = await capsule_repo.get_capsule_templates(
        db, element_id=element_id, rarity_id=rarity_id, is_available=True
    )

    return {
        "ok": True,
        "data": {
            "capsules": [CapsuleTemplateResponse.from_orm(t) for t in templates],
            "total_count": len(templates),
        },
        "error": None,
    }


@router.post("/capsules/buy", response_model=dict)
async def buy_capsule(
    buy_request: CapsuleBuyRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Покупка капсулы
    """
    # Получаем шаблон капсулы
    capsule_template = await capsule_repo.get_capsule_template(db, buy_request.capsule_id)
    if not capsule_template:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Capsule template not found"},
        }

    if not capsule_template.is_available:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Capsule is not available for purchase"},
        }

    # Проверяем количество в наличии
    if capsule_template.amount > 0 and buy_request.quantity > capsule_template.amount:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Not enough capsules in stock"},
        }

    # Вычисляем стоимость
    currency = buy_request.pay_with.upper()
    if currency == "TON":
        total_price = capsule_template.price_in_ton * buy_request.quantity
    elif currency == "LUMENS":
        total_price = capsule_template.price_lumens * buy_request.quantity
    else:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Invalid currency. Use 'ton' or 'lumens'"},
        }

    # Проверяем баланс пользователя
    user = await user_repo.get_user_by_tg_id(db, current_user_id)
    if not user:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "User not found"},
        }

    current_balance = user.ton_balance if currency == "TON" else user.lumens_balance
    if current_balance < total_price:
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "INSUFFICIENT_FUNDS",
                "message": f"Insufficient {currency} balance. Required: {total_price}, Available: {current_balance}",
            },
        }

    try:
        async with db.begin():
            # Списываем баланс
            await user_repo.subtract_balance(
                db,
                current_user_id,
                total_price,
                currency,
                f"capsule_purchase_{capsule_template.code}"
            )

            # Проверяем, есть ли уже такая капсула у игрока
            player_capsules = await capsule_repo.get_player_capsules(db, current_user_id)
            existing_capsule = next(
                (pc for pc in player_capsules if pc.capsule_id == buy_request.capsule_id and not pc.is_opened and not pc.is_opening),
                None
            )

            if existing_capsule:
                # Увеличиваем количество
                player_capsule = await capsule_repo.update_player_capsule_quantity(
                    db, existing_capsule.id, existing_capsule.quantity + buy_request.quantity
                )
            else:
                # Создаем новую запись
                player_capsule = await capsule_repo.create_player_capsule(
                    db, current_user_id, buy_request.capsule_id, buy_request.quantity
                )

            # Обновляем количество в шаблоне, если оно ограничено
            if capsule_template.amount > 0:
                await capsule_repo.update_capsule_template(
                    db,
                    capsule_template.id,
                    {"amount": capsule_template.amount - buy_request.quantity}
                )

        await db.commit()
        await db.refresh(player_capsule)

        return {
            "ok": True,
            "data": CapsuleBuyResponse(
                player_capsule=PlayerCapsuleResponse.from_orm(player_capsule),
                balance_change=-total_price,
                currency=currency,
            ),
            "error": None,
        }

    except ValueError as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": str(e)},
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to purchase capsule"},
        }


@router.get("/capsules/my", response_model=dict)
async def get_my_capsules(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Получение капсул игрока
    """
    capsules = await capsule_repo.get_player_capsules(db, current_user_id)

    return {
        "ok": True,
        "data": {
            "capsules": [PlayerCapsuleResponse.from_orm(c) for c in capsules],
            "total_count": len(capsules),
        },
        "error": None,
    }


@router.post("/capsules/{capsule_id}/open", response_model=dict)
async def open_capsule(
    capsule_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Открытие капсулы
    - Если open_time=0: синхронное открытие с weighted random
    - Если open_time>0: асинхронное открытие через Celery (Sprint 4)
    """
    from backend.services.capsule_service import open_capsule_synchronous
    from backend.schemas.spirit import PlayerSpiritResponse

    # Получаем капсулу игрока
    player_capsule = await capsule_repo.get_player_capsule(db, capsule_id, current_user_id)
    if not player_capsule:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Capsule not found or you don't own it"},
        }

    if player_capsule.is_opened:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Capsule is already opened"},
        }

    if player_capsule.is_opening:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "ALREADY_OPENING", "message": "Capsule is already being opened"},
        }

    if player_capsule.quantity <= 0:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "No capsules to open"},
        }

    # Проверяем open_time
    capsule_template = player_capsule.template
    if not capsule_template:
        capsule_template = await capsule_repo.get_capsule_template(db, player_capsule.capsule_id)

    if capsule_template.open_time_seconds == 0:
        # Синхронное открытие
        result = await open_capsule_synchronous(db, capsule_id, current_user_id)

        if not result["success"]:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "INTERNAL_ERROR", "message": result["error"]},
            }

        return {
            "ok": True,
            "data": {
                "message": "Capsule opened successfully!",
                "spirit": PlayerSpiritResponse.from_orm(result["spirit"]),
            },
            "error": None,
        }
    else:
        # Асинхронное открытие (Sprint 4)
        from datetime import datetime, timedelta
        from workers.tasks.capsules import finish_capsule_opening

        try:
            async with db.begin():
                # Устанавливаем флаг is_opening
                await capsule_repo.update_player_capsule(
                    db,
                    capsule_id,
                    is_opening=True
                )

            await db.commit()

            # Планируем Celery задачу на завершение открытия через open_time_seconds
            finish_capsule_opening.apply_async(
                args=[capsule_id, current_user_id],
                countdown=capsule_template.open_time_seconds
            )

            return {
                "ok": True,
                "data": {
                    "message": "Capsule opening started",
                    "will_open_at": (datetime.utcnow() + timedelta(seconds=capsule_template.open_time_seconds)).isoformat(),
                    "open_time_seconds": capsule_template.open_time_seconds,
                },
                "error": None,
            }

        except Exception as e:
            await db.rollback()
            return {
                "ok": False,
                "data": None,
                "error": {"code": "INTERNAL_ERROR", "message": "Failed to start capsule opening"},
            }


@router.post("/capsules/{capsule_id}/fast_open", response_model=dict)
async def fast_open_capsule(
    capsule_id: int,
    fast_open_request: CapsuleFastOpenRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Быстрое открытие капсулы за TON/Lumens
    Позволяет мгновенно открыть капсулу, которая находится в процессе открытия
    """
    from backend.services.capsule_service import open_capsule_synchronous
    from backend.schemas.spirit import PlayerSpiritResponse

    # Получаем капсулу игрока
    player_capsule = await capsule_repo.get_player_capsule(db, capsule_id, current_user_id)
    if not player_capsule:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Capsule not found or you don't own it"},
        }

    if not player_capsule.is_opening:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Capsule is not currently being opened"},
        }

    # Получаем шаблон капсулы для информации о fast_open_cost
    capsule_template = player_capsule.template
    if not capsule_template:
        capsule_template = await capsule_repo.get_capsule_template(db, player_capsule.capsule_id)

    # Определяем стоимость
    currency = fast_open_request.pay_with.upper()
    if currency == "TON":
        cost = capsule_template.fast_open_cost_ton or Decimal("0.05")
    elif currency == "LUMENS":
        cost = capsule_template.fast_open_cost_lumens or Decimal("25")
    else:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Invalid currency. Use 'ton' or 'lumens'"},
        }

    # Проверяем баланс
    user = await user_repo.get_user_by_tg_id(db, current_user_id)
    if not user:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "User not found"},
        }

    current_balance = user.ton_balance if currency == "TON" else user.lumens_balance
    if current_balance < cost:
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "INSUFFICIENT_FUNDS",
                "message": f"Insufficient {currency} balance. Required: {cost}, Available: {current_balance}",
            },
        }

    try:
        async with db.begin():
            # Списываем баланс
            await user_repo.subtract_balance(
                db,
                current_user_id,
                cost,
                currency,
                f"fast_open_capsule_{capsule_id}"
            )

            # Снимаем флаг is_opening
            await capsule_repo.update_player_capsule(
                db,
                capsule_id,
                is_opening=False
            )

        await db.commit()

        # Открываем капсулу мгновенно
        result = await open_capsule_synchronous(db, capsule_id, current_user_id)

        if not result["success"]:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "INTERNAL_ERROR", "message": result["error"]},
            }

        return {
            "ok": True,
            "data": {
                "message": "Capsule opened instantly!",
                "spirit": PlayerSpiritResponse.from_orm(result["spirit"]),
                "balance_change": -cost,
                "currency": currency,
            },
            "error": None,
        }

    except ValueError as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": str(e)},
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to fast open capsule"},
        }
