"""
API эндпоинты для слотов
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List, Optional

from backend.db.session import get_db
from backend.schemas.slot import (
    SlotTemplateResponse,
    PlayerSlotResponse,
    SlotBuyRequest,
    SlotBuyResponse,
    SlotSellRequest,
)
from backend.db.repository import slot as slot_repo
from backend.db.repository import user as user_repo
from backend.db.repository import spirit as spirit_repo
from backend.core.security import get_current_user_id

router = APIRouter()


@router.get("/slots/templates", response_model=dict)
async def get_slot_templates(
    element_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Получение доступных шаблонов слотов
    """
    templates = await slot_repo.get_slot_templates(db, element_id=element_id, is_available=True)

    return {
        "ok": True,
        "data": {
            "slots": [SlotTemplateResponse.from_orm(t) for t in templates],
            "total_count": len(templates),
        },
        "error": None,
    }


@router.post("/slots/buy", response_model=dict)
async def buy_slot(
    buy_request: SlotBuyRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Покупка слота
    """
    # Получаем шаблон слота
    slot_template = await slot_repo.get_slot_template(db, buy_request.slot_template_id)
    if not slot_template:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Slot template not found"},
        }

    if not slot_template.is_available:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Slot is not available for purchase"},
        }

    # Вычисляем стоимость
    currency = buy_request.pay_with.upper()
    if currency != "LUMENS":
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Slots can only be purchased with Lumens"},
        }

    price = slot_template.price_lumens

    # Проверяем баланс пользователя
    user = await user_repo.get_user_by_tg_id(db, current_user_id)
    if not user:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "User not found"},
        }

    if user.lumens_balance < price:
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "INSUFFICIENT_FUNDS",
                "message": f"Insufficient Lumens balance. Required: {price}, Available: {user.lumens_balance}",
            },
        }

    try:
        async with db.begin():
            # Списываем баланс
            await user_repo.subtract_balance(
                db,
                current_user_id,
                price,
                currency,
                f"slot_purchase_element_{slot_template.element_id}"
            )

            # Создаем слот
            player_slot = await slot_repo.create_player_slot(
                db,
                current_user_id,
                buy_request.slot_template_id,
                slot_template.element_id
            )

        await db.commit()
        await db.refresh(player_slot)

        return {
            "ok": True,
            "data": SlotBuyResponse(
                player_slot=PlayerSlotResponse.from_orm(player_slot),
                balance_change=-price,
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
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to purchase slot"},
        }


@router.post("/slots/sell", response_model=dict)
async def sell_slot(
    sell_request: SlotSellRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Продажа слота
    Возвращает sell_price_lumens обратно игроку
    """
    # Получаем слот игрока
    player_slot = await slot_repo.get_player_slot(db, sell_request.player_slot_id, current_user_id)
    if not player_slot:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Slot not found or you don't own it"},
        }

    # Проверяем, не занят ли слот спиритом
    active_spirits = await spirit_repo.get_active_spirits(db, current_user_id)
    for spirit in active_spirits:
        if spirit.slot_id == player_slot.id:
            return {
                "ok": False,
                "data": None,
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "Cannot sell slot with active spirit. Deactivate spirit first."
                },
            }

    # Получаем шаблон для определения цены продажи
    slot_template = player_slot.template
    if not slot_template:
        slot_template = await slot_repo.get_slot_template(db, player_slot.slot_template_id)

    sell_price = slot_template.sell_price_lumens

    try:
        async with db.begin():
            # Удаляем слот
            await slot_repo.delete_player_slot(db, sell_request.player_slot_id)

            # Возвращаем деньги
            if sell_price > 0:
                await user_repo.add_balance(
                    db,
                    current_user_id,
                    sell_price,
                    "LUMENS",
                    f"slot_sold_element_{slot_template.element_id}"
                )

        await db.commit()

        return {
            "ok": True,
            "data": {
                "message": "Slot sold successfully",
                "refund_amount": sell_price,
                "currency": "LUMENS",
            },
            "error": None,
        }

    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to sell slot"},
        }


@router.get("/slots/party", response_model=dict)
async def get_party(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Получение активной партии (слоты + спириты)
    Аналогично /spirits/active, но фокус на слотах
    """
    slots = await slot_repo.get_player_slots(db, current_user_id)
    active_spirits = await spirit_repo.get_active_spirits(db, current_user_id)

    # Создаем словарь спиритов по slot_id
    spirits_by_slot = {s.slot_id: s for s in active_spirits if s.slot_id}

    # Формируем партию
    party = []
    for slot in slots:
        spirit = spirits_by_slot.get(slot.id)
        party.append({
            "slot": PlayerSlotResponse.from_orm(slot),
            "spirit": {
                "id": spirit.id,
                "custom_name": spirit.custom_name,
                "level": spirit.level,
                "xp": spirit.xp,
                "energy": spirit.energy,
                "is_minted": spirit.is_minted,
            } if spirit else None,
        })

    return {
        "ok": True,
        "data": {
            "party": party,
            "total_slots": len(slots),
            "filled_slots": len(active_spirits),
            "empty_slots": len(slots) - len(active_spirits),
        },
        "error": None,
    }


@router.get("/slots/my", response_model=dict)
async def get_my_slots(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Получение всех слотов игрока
    """
    slots = await slot_repo.get_player_slots(db, current_user_id)

    return {
        "ok": True,
        "data": {
            "slots": [PlayerSlotResponse.from_orm(s) for s in slots],
            "total_count": len(slots),
        },
        "error": None,
    }
