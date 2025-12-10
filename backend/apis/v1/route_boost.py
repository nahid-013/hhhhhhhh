"""
API эндпоинты для бустов
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List

from backend.db.session import get_db
from backend.schemas.boost import (
    BoostTemplateResponse,
    PlayerBoostResponse,
    BoostBuyRequest,
    BoostBuyResponse,
    BoostUseRequest,
)
from backend.db.repository import boost as boost_repo
from backend.db.repository import user as user_repo
from backend.db.repository import spirit as spirit_repo
from backend.core.security import get_current_user_id

router = APIRouter()


@router.get("/boosts/shop", response_model=dict)
async def get_boost_shop(
    db: AsyncSession = Depends(get_db),
):
    """
    Получение магазина бустов
    """
    templates = await boost_repo.get_boost_templates(db, is_available=True)

    return {
        "ok": True,
        "data": {
            "boosts": [BoostTemplateResponse.from_orm(t) for t in templates],
            "total_count": len(templates),
        },
        "error": None,
    }


@router.post("/boosts/buy", response_model=dict)
async def buy_boost(
    buy_request: BoostBuyRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Покупка буста
    """
    # Получаем шаблон буста
    boost_template = await boost_repo.get_boost_template(db, buy_request.boost_id)
    if not boost_template:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Boost template not found"},
        }

    if not boost_template.is_available:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Boost is not available for purchase"},
        }

    # Проверяем количество в наличии
    if boost_template.amount > 0 and buy_request.quantity > boost_template.amount:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Not enough boosts in stock"},
        }

    # Вычисляем стоимость
    currency = buy_request.pay_with.upper()
    if currency == "TON":
        total_price = boost_template.price_ton * buy_request.quantity
    elif currency == "LUMENS":
        # Бусты обычно покупаются только за TON, но оставляем возможность
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Boosts can only be purchased with TON"},
        }
    else:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Invalid currency. Use 'ton'"},
        }

    # Проверяем баланс пользователя
    user = await user_repo.get_user_by_tg_id(db, current_user_id)
    if not user:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "User not found"},
        }

    if user.ton_balance < total_price:
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "INSUFFICIENT_FUNDS",
                "message": f"Insufficient TON balance. Required: {total_price}, Available: {user.ton_balance}",
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
                f"boost_purchase_{boost_template.internal_name}"
            )

            # Создаем или обновляем буст игрока
            player_boost = await boost_repo.get_or_create_player_boost(
                db, current_user_id, buy_request.boost_id, buy_request.quantity
            )

            # Обновляем количество в шаблоне, если оно ограничено
            if boost_template.amount > 0:
                await boost_repo.update_boost_template(
                    db,
                    boost_template.id,
                    {"amount": boost_template.amount - buy_request.quantity}
                )

        await db.commit()
        await db.refresh(player_boost)

        return {
            "ok": True,
            "data": BoostBuyResponse(
                player_boost=PlayerBoostResponse.from_orm(player_boost),
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
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to purchase boost"},
        }


@router.get("/boosts/my", response_model=dict)
async def get_my_boosts(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Получение бустов игрока
    """
    boosts = await boost_repo.get_player_boosts(db, current_user_id)

    return {
        "ok": True,
        "data": {
            "boosts": [PlayerBoostResponse.from_orm(b) for b in boosts],
            "total_count": len(boosts),
        },
        "error": None,
    }


@router.post("/boosts/use", response_model=dict)
async def use_boost(
    use_request: BoostUseRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Использование буста на спирита
    Применяет boost_xp к спириту и обрабатывает level up если нужно

    Формула level up: xp_for_next_level = floor(100 * level^1.2)
    """
    # Получаем буст игрока
    player_boost = await boost_repo.get_player_boost(
        db, use_request.player_boost_id, current_user_id
    )
    if not player_boost:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Boost not found or you don't own it"},
        }

    if player_boost.quantity <= 0:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "No boosts available to use"},
        }

    # Получаем спирита
    player_spirit = await spirit_repo.get_player_spirit(
        db, use_request.player_spirit_id, current_user_id
    )
    if not player_spirit:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Spirit not found or you don't own it"},
        }

    try:
        async with db.begin():
            # Получаем шаблон буста для информации о XP
            boost_template = player_boost.template
            if not boost_template:
                boost_template = await boost_repo.get_boost_template(db, player_boost.boost_id)

            # Применяем XP к спириту
            await spirit_repo.add_xp_to_spirit(
                db,
                player_spirit.id,
                boost_template.boost_xp
            )

            # Уменьшаем количество бустов
            await boost_repo.update_player_boost_quantity(
                db, player_boost.id, player_boost.quantity - 1
            )

        await db.commit()

        # Обновляем спирита для получения актуальных данных
        player_spirit = await spirit_repo.get_player_spirit(
            db, use_request.player_spirit_id, current_user_id
        )

        return {
            "ok": True,
            "data": {
                "message": "Boost applied successfully",
                "xp_added": boost_template.boost_xp,
                "spirit": {
                    "id": player_spirit.id,
                    "level": player_spirit.level,
                    "xp": player_spirit.xp,
                    "custom_name": player_spirit.custom_name,
                },
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
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to use boost"},
        }
