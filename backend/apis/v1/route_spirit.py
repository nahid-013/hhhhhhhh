"""
API эндпоинты для спиритов
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import List, Optional

from backend.db.session import get_db
from backend.schemas.spirit import (
    SpiritTemplateResponse,
    PlayerSpiritResponse,
    SpiritActivateRequest,
    SpiritRenameRequest,
    SpiritRestoreEnergyRequest,
    SpiritRestoreEnergyResponse,
    SpiritBreedRequest,
    SpiritBreedResponse,
)
from backend.db.repository import spirit as spirit_repo
from backend.db.repository import slot as slot_repo
from backend.db.repository import user as user_repo
from backend.core.security import get_current_user_id

router = APIRouter()


@router.get("/spirits/catalog", response_model=dict)
async def get_spirit_catalog(
    element_id: Optional[int] = None,
    rarity_id: Optional[int] = None,
    generation: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Получение каталога шаблонов спиритов
    """
    templates = await spirit_repo.get_spirit_templates(
        db,
        element_id=element_id,
        rarity_id=rarity_id,
        generation=generation,
        is_available=True
    )

    return {
        "ok": True,
        "data": {
            "spirits": [SpiritTemplateResponse.from_orm(t) for t in templates],
            "total_count": len(templates),
        },
        "error": None,
    }


@router.get("/spirits/my", response_model=dict)
async def get_my_spirits(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Получение всех спиритов игрока
    """
    spirits = await spirit_repo.get_player_spirits(db, current_user_id)

    return {
        "ok": True,
        "data": {
            "spirits": [PlayerSpiritResponse.from_orm(s) for s in spirits],
            "total_count": len(spirits),
        },
        "error": None,
    }


@router.get("/spirits/active", response_model=dict)
async def get_active_party(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Получение активной партии (слоты + активные спириты)
    """
    active_spirits = await spirit_repo.get_active_spirits(db, current_user_id)
    all_slots = await slot_repo.get_player_slots(db, current_user_id)

    # Создаем словарь спиритов по slot_id для быстрого доступа
    spirits_by_slot = {s.slot_id: s for s in active_spirits if s.slot_id}

    # Формируем партию
    party = []
    for slot in all_slots:
        spirit = spirits_by_slot.get(slot.id)
        party.append({
            "slot": {
                "id": slot.id,
                "element_id": slot.element_id,
                "slot_template_id": slot.slot_template_id,
            },
            "spirit": PlayerSpiritResponse.from_orm(spirit) if spirit else None,
        })

    return {
        "ok": True,
        "data": {
            "party": party,
            "total_slots": len(all_slots),
            "filled_slots": len(active_spirits),
        },
        "error": None,
    }


@router.post("/spirits/{spirit_id}/activate", response_model=dict)
async def activate_spirit(
    spirit_id: int,
    activate_request: SpiritActivateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Активация спирита в слот
    Проверяет совместимость element_id
    """
    # Получаем спирита
    player_spirit = await spirit_repo.get_player_spirit(db, spirit_id, current_user_id)
    if not player_spirit:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Spirit not found or you don't own it"},
        }

    # Получаем слот
    player_slot = await slot_repo.get_player_slot(db, activate_request.player_slot_id, current_user_id)
    if not player_slot:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Slot not found or you don't own it"},
        }

    # Получаем template спирита для проверки element_id
    spirit_template = player_spirit.template
    if not spirit_template:
        spirit_template = await spirit_repo.get_spirit_template(db, player_spirit.spirit_template_id)

    # Проверяем совместимость element_id
    if spirit_template.element_id != player_slot.element_id:
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "COMPATIBILITY_ERROR",
                "message": "Spirit element doesn't match slot element"
            },
        }

    # Проверяем, не занят ли слот другим спиритом
    active_spirits = await spirit_repo.get_active_spirits(db, current_user_id)
    for active in active_spirits:
        if active.slot_id == activate_request.player_slot_id and active.id != spirit_id:
            # Деактивируем предыдущего спирита в этом слоте
            await spirit_repo.deactivate_spirit(db, active.id)

    try:
        async with db.begin():
            # Если спирит уже активен в другом слоте, сначала деактивируем
            if player_spirit.is_active:
                await spirit_repo.deactivate_spirit(db, spirit_id)

            # Активируем спирита в новом слоте
            updated_spirit = await spirit_repo.activate_spirit(
                db, spirit_id, activate_request.player_slot_id
            )

        await db.commit()

        return {
            "ok": True,
            "data": {
                "message": "Spirit activated successfully",
                "spirit": PlayerSpiritResponse.from_orm(updated_spirit),
            },
            "error": None,
        }

    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to activate spirit"},
        }


@router.post("/spirits/{spirit_id}/deactivate", response_model=dict)
async def deactivate_spirit_endpoint(
    spirit_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Деактивация спирита (убрать из слота)
    """
    player_spirit = await spirit_repo.get_player_spirit(db, spirit_id, current_user_id)
    if not player_spirit:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Spirit not found or you don't own it"},
        }

    if not player_spirit.is_active:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Spirit is not active"},
        }

    updated_spirit = await spirit_repo.deactivate_spirit(db, spirit_id)
    await db.commit()

    return {
        "ok": True,
        "data": {
            "message": "Spirit deactivated successfully",
            "spirit": PlayerSpiritResponse.from_orm(updated_spirit),
        },
        "error": None,
    }


@router.patch("/spirits/{spirit_id}/rename", response_model=dict)
async def rename_spirit(
    spirit_id: int,
    rename_request: SpiritRenameRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Переименование спирита
    """
    player_spirit = await spirit_repo.get_player_spirit(db, spirit_id, current_user_id)
    if not player_spirit:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Spirit not found or you don't own it"},
        }

    updated_spirit = await spirit_repo.update_player_spirit(
        db, spirit_id, custom_name=rename_request.custom_name
    )
    await db.commit()

    return {
        "ok": True,
        "data": {
            "message": "Spirit renamed successfully",
            "spirit": PlayerSpiritResponse.from_orm(updated_spirit),
        },
        "error": None,
    }


@router.post("/spirits/{spirit_id}/restore_energy", response_model=dict)
async def restore_spirit_energy(
    spirit_id: int,
    restore_request: SpiritRestoreEnergyRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Мгновенное восстановление энергии спирита за TON/Lumens

    Цены:
    - TON: 0.1 TON за полное восстановление
    - Lumens: 50 Lumens за полное восстановление
    """
    from backend.core.config import settings

    # Получаем спирита
    player_spirit = await spirit_repo.get_player_spirit(db, spirit_id, current_user_id)
    if not player_spirit:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Spirit not found or you don't own it"},
        }

    # Вычисляем max_energy
    max_energy = player_spirit.base_max_energy + (player_spirit.generation * 5)

    # Проверяем, что энергия не полная
    if player_spirit.energy >= max_energy:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Spirit energy is already full"},
        }

    # Определяем стоимость
    currency = restore_request.pay_with.upper()
    if currency == "TON":
        cost = Decimal("0.1")
    elif currency == "LUMENS":
        cost = Decimal("50")
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

    # TODO: Проверка rate limiting (max N восстановлений за 24ч)
    # Будет реализовано после добавления Redis rate limiting

    try:
        previous_energy = player_spirit.energy

        async with db.begin():
            # Списываем баланс
            await user_repo.subtract_balance(
                db,
                current_user_id,
                cost,
                currency,
                f"energy_restore_spirit_{spirit_id}"
            )

            # Восстанавливаем энергию
            await spirit_repo.update_player_spirit(
                db,
                spirit_id,
                energy=max_energy
            )

        await db.commit()
        await db.refresh(player_spirit)

        return {
            "ok": True,
            "data": SpiritRestoreEnergyResponse(
                spirit=PlayerSpiritResponse.from_orm(player_spirit),
                previous_energy=previous_energy,
                new_energy=max_energy,
                max_energy=max_energy,
                balance_change=-cost,
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
            "error": {"code": "INTERNAL_ERROR", "message": "Failed to restore energy"},
        }


@router.post("/spirits/{spirit_id}/mint", response_model=dict)
async def mint_spirit_nft(
    spirit_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Минт NFT для спирита

    Требования:
    - Spirit принадлежит current user
    - Spirit еще не смитнчен
    - Достаточно TON для mint fee (0.1 TON)

    После минта:
    - is_minted = true
    - nft_id = collection_address:token_id
    """
    from backend.services import nft_client

    # Mint fee
    MINT_FEE = Decimal("0.1")

    player_spirit = await spirit_repo.get_player_spirit(db, spirit_id, current_user_id)
    if not player_spirit:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Spirit not found or you don't own it"},
        }

    if player_spirit.is_minted:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Spirit is already minted as NFT"},
        }

    # Проверяем баланс
    user = await user_repo.get_user_by_tg_id(db, current_user_id)
    if not user:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "User not found"},
        }

    if user.ton_balance < MINT_FEE:
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "INSUFFICIENT_FUNDS",
                "message": f"Insufficient TON balance. Required: {MINT_FEE}, Available: {user.ton_balance}",
            },
        }

    # Проверяем что у пользователя подключен кошелек
    if not user.ton_address:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "WALLET_NOT_CONNECTED", "message": "Please connect your TON wallet first"},
        }

    try:
        # Готовим metadata для NFT
        template = player_spirit.template
        if not template:
            template = await spirit_repo.get_spirit_template(db, player_spirit.spirit_template_id)

        metadata = {
            "name": player_spirit.custom_name or template.name_en,
            "description": player_spirit.description_en or template.description_en,
            "image": template.icon_url,
            "attributes": {
                "generation": player_spirit.generation,
                "level": player_spirit.level,
                "element": template.element_id,
                "rarity": template.rarity_id,
                "run": player_spirit.base_run,
                "jump": player_spirit.base_jump,
                "swim": player_spirit.base_swim,
                "dives": player_spirit.base_dives,
                "fly": player_spirit.base_fly,
                "maneuver": player_spirit.base_maneuver,
            }
        }

        # Вызываем NFT Service для минта
        nft_result = await nft_client.mint_nft(
            player_spirit_id=spirit_id,
            owner_address=user.ton_address,
            metadata=metadata
        )

        async with db.begin():
            # Списываем TON
            await user_repo.subtract_balance(
                db,
                current_user_id,
                MINT_FEE,
                "TON",
                f"nft_mint_spirit_{spirit_id}"
            )

            # Обновляем спирита
            await spirit_repo.update_player_spirit(
                db,
                spirit_id,
                is_minted=True,
                nft_id=nft_result["nft_id"]
            )

        await db.commit()
        await db.refresh(player_spirit)

        return {
            "ok": True,
            "data": {
                "message": "Spirit minted as NFT successfully!",
                "spirit": PlayerSpiritResponse.from_orm(player_spirit),
                "nft_id": nft_result["nft_id"],
                "tx_hash": nft_result["tx_hash"],
                "balance_change": -MINT_FEE,
            },
            "error": None,
        }

    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "MINT_FAILED", "message": f"Failed to mint NFT: {str(e)}"},
        }


@router.post("/spirits/{spirit_id}/burn", response_model=dict)
async def burn_spirit_nft(
    spirit_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Сжигание NFT спирита

    Требования:
    - Spirit принадлежит current user
    - Spirit должен быть смитнчен (is_minted = true)
    - Небольшой lumens fee

    После burn:
    - is_minted = false
    - nft_id = null
    - Спирит остается в БД, но теряет NFT статус
    """
    from backend.services import ton_client

    # Burn fee (небольшой, чтобы не злоупотребляли)
    BURN_FEE = Decimal("50.0")  # 50 Lumens

    player_spirit = await spirit_repo.get_player_spirit(db, spirit_id, current_user_id)
    if not player_spirit:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "Spirit not found or you don't own it"},
        }

    if not player_spirit.is_minted:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Spirit is not minted as NFT"},
        }

    if not player_spirit.nft_id:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INVALID_INPUT", "message": "Spirit has no NFT ID"},
        }

    # Проверяем баланс Lumens
    user = await user_repo.get_user_by_tg_id(db, current_user_id)
    if not user:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NOT_FOUND", "message": "User not found"},
        }

    if user.lumens_balance < BURN_FEE:
        return {
            "ok": False,
            "data": None,
            "error": {
                "code": "INSUFFICIENT_FUNDS",
                "message": f"Insufficient Lumens balance. Required: {BURN_FEE}, Available: {user.lumens_balance}",
            },
        }

    # Проверяем что у пользователя подключен кошелек
    if not user.ton_address:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "WALLET_NOT_CONNECTED", "message": "Please connect your TON wallet first"},
        }

    try:
        # Вызываем TON Service для burn NFT
        burn_result = await ton_client.burn_nft(
            nft_id=player_spirit.nft_id,
            owner_address=user.ton_address
        )

        async with db.begin():
            # Списываем Lumens
            await user_repo.subtract_balance(
                db,
                current_user_id,
                BURN_FEE,
                "LUMENS",
                f"nft_burn_spirit_{spirit_id}"
            )

            # Обновляем спирита - убираем NFT статус
            await spirit_repo.update_player_spirit(
                db,
                spirit_id,
                is_minted=False,
                nft_id=None
            )

        await db.commit()
        await db.refresh(player_spirit)

        return {
            "ok": True,
            "data": {
                "message": "NFT burned successfully!",
                "spirit": PlayerSpiritResponse.from_orm(player_spirit),
                "tx_hash": burn_result["tx_hash"],
                "lumens_fee": -BURN_FEE,
            },
            "error": None,
        }

    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "BURN_FAILED", "message": f"Failed to burn NFT: {str(e)}"},
        }


@router.post("/spirits/breed", response_model=dict)
async def breed_spirits(
    breed_request: SpiritBreedRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Скрещивание двух спиритов для создания потомка

    Требования:
    - Оба родителя принадлежат current user
    - Одинаковый element_id
    - Одинаковый spirit_template_id
    - Оба level == 10
    - Достаточно TON для breeding cost

    Формулы:
    - child_gen = min(parent1_gen, parent2_gen) + 1
    - child_stat = max(parent1_stat, parent2_stat, MIN_STATS[gen])
    - rarity = max(parent1_rarity, parent2_rarity)

    Родители будут уничтожены (burn) после создания потомка
    """
    from backend.services.breeding_service import breed_spirits as breed_spirits_service

    # Выполняем breeding через сервис
    result = await breed_spirits_service(
        db,
        breed_request.parent1_id,
        breed_request.parent2_id,
        current_user_id
    )

    if not result["success"]:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "BREEDING_FAILED", "message": result["error"]},
        }

    # Обновляем child для получения актуальных данных с relationships
    child_spirit = await spirit_repo.get_player_spirit(db, result["child"].id, current_user_id)

    return {
        "ok": True,
        "data": SpiritBreedResponse(
            child_spirit=PlayerSpiritResponse.from_orm(child_spirit),
            balance_change=-result["cost"],
            currency="TON",
            message=f"Breeding successful! New {child_spirit.generation}th generation spirit created.",
        ),
        "error": None,
    }
