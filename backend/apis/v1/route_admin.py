"""
API эндпоинты для администрирования
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.core.security import get_current_admin_user, verify_admin_access

# Импорты схем
from backend.schemas.capsule import (
    CapsuleTemplateCreate,
    CapsuleTemplateUpdate,
    CapsuleTemplateResponse
)
from backend.schemas.boost import (
    BoostTemplateCreate,
    BoostTemplateUpdate,
    BoostTemplateResponse
)
from backend.schemas.spirit import (
    SpiritTemplateCreate,
    SpiritTemplateUpdate,
    SpiritTemplateResponse
)
from backend.schemas.slot import (
    SlotTemplateCreate,
    SlotTemplateUpdate,
    SlotTemplateResponse
)

# Импорты репозиториев
from backend.db.repository import capsule as capsule_repo
from backend.db.repository import boost as boost_repo
from backend.db.repository import spirit as spirit_repo
from backend.db.repository import slot as slot_repo

router = APIRouter()


# =======================
# CAPSULE TEMPLATES CRUD
# =======================

@router.post("/admin/capsules", response_model=dict)
async def create_capsule_template(
    capsule_data: CapsuleTemplateCreate,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Создать новый шаблон капсулы (только для админов)
    """
    # Проверка прав администратора
    await verify_admin_access(db, admin_user_id)

    try:
        capsule = await capsule_repo.create_capsule_template(db, capsule_data)
        await db.commit()
        return {
            "ok": True,
            "data": CapsuleTemplateResponse.model_validate(capsule),
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.patch("/admin/capsules/{capsule_id}", response_model=dict)
async def update_capsule_template(
    capsule_id: int,
    capsule_data: CapsuleTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Обновить шаблон капсулы (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        capsule = await capsule_repo.update_capsule_template(db, capsule_id, capsule_data)
        if not capsule:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "Capsule template not found"}
            }

        await db.commit()
        return {
            "ok": True,
            "data": CapsuleTemplateResponse.model_validate(capsule),
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.delete("/admin/capsules/{capsule_id}", response_model=dict)
async def delete_capsule_template(
    capsule_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Удалить/деактивировать шаблон капсулы (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        # Мягкое удаление - устанавливаем is_available = False
        capsule_data = CapsuleTemplateUpdate(is_available=False)
        capsule = await capsule_repo.update_capsule_template(db, capsule_id, capsule_data)

        if not capsule:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "Capsule template not found"}
            }

        await db.commit()
        return {
            "ok": True,
            "data": {"message": "Capsule template deactivated"},
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


# =======================
# BOOST TEMPLATES CRUD
# =======================

@router.post("/admin/boosts", response_model=dict)
async def create_boost_template(
    boost_data: BoostTemplateCreate,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Создать новый шаблон буста (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        boost = await boost_repo.create_boost_template(db, boost_data)
        await db.commit()
        return {
            "ok": True,
            "data": BoostTemplateResponse.model_validate(boost),
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.patch("/admin/boosts/{boost_id}", response_model=dict)
async def update_boost_template(
    boost_id: int,
    boost_data: BoostTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Обновить шаблон буста (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        boost = await boost_repo.update_boost_template(db, boost_id, boost_data)
        if not boost:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "Boost template not found"}
            }

        await db.commit()
        return {
            "ok": True,
            "data": BoostTemplateResponse.model_validate(boost),
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.delete("/admin/boosts/{boost_id}", response_model=dict)
async def delete_boost_template(
    boost_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Удалить/деактивировать шаблон буста (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        # Мягкое удаление
        boost_data = BoostTemplateUpdate(is_available=False)
        boost = await boost_repo.update_boost_template(db, boost_id, boost_data)

        if not boost:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "Boost template not found"}
            }

        await db.commit()
        return {
            "ok": True,
            "data": {"message": "Boost template deactivated"},
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


# =======================
# SPIRIT TEMPLATES CRUD
# =======================

@router.post("/admin/spirits", response_model=dict)
async def create_spirit_template(
    spirit_data: SpiritTemplateCreate,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Создать новый шаблон спирита (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        spirit = await spirit_repo.create_spirit_template(db, spirit_data)
        await db.commit()
        return {
            "ok": True,
            "data": SpiritTemplateResponse.model_validate(spirit),
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.patch("/admin/spirits/{spirit_id}", response_model=dict)
async def update_spirit_template(
    spirit_id: int,
    spirit_data: SpiritTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Обновить шаблон спирита (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        spirit = await spirit_repo.update_spirit_template(db, spirit_id, spirit_data)
        if not spirit:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "Spirit template not found"}
            }

        await db.commit()
        return {
            "ok": True,
            "data": SpiritTemplateResponse.model_validate(spirit),
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.delete("/admin/spirits/{spirit_id}", response_model=dict)
async def delete_spirit_template(
    spirit_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Удалить/деактивировать шаблон спирита (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        # Мягкое удаление
        spirit_data = SpiritTemplateUpdate(is_available=False)
        spirit = await spirit_repo.update_spirit_template(db, spirit_id, spirit_data)

        if not spirit:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "Spirit template not found"}
            }

        await db.commit()
        return {
            "ok": True,
            "data": {"message": "Spirit template deactivated"},
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


# =======================
# SLOT TEMPLATES CRUD
# =======================

@router.post("/admin/slots", response_model=dict)
async def create_slot_template(
    slot_data: SlotTemplateCreate,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Создать новый шаблон слота (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        slot = await slot_repo.create_slot_template(db, slot_data)
        await db.commit()
        return {
            "ok": True,
            "data": SlotTemplateResponse.model_validate(slot),
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.patch("/admin/slots/{slot_id}", response_model=dict)
async def update_slot_template(
    slot_id: int,
    slot_data: SlotTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Обновить шаблон слота (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        slot = await slot_repo.update_slot_template(db, slot_id, slot_data)
        if not slot:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "Slot template not found"}
            }

        await db.commit()
        return {
            "ok": True,
            "data": SlotTemplateResponse.model_validate(slot),
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }


@router.delete("/admin/slots/{slot_id}", response_model=dict)
async def delete_slot_template(
    slot_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user_id: int = Depends(get_current_admin_user),
):
    """
    Удалить/деактивировать шаблон слота (только для админов)
    """
    await verify_admin_access(db, admin_user_id)

    try:
        # Мягкое удаление
        slot_data = SlotTemplateUpdate(is_available=False)
        slot = await slot_repo.update_slot_template(db, slot_id, slot_data)

        if not slot:
            return {
                "ok": False,
                "data": None,
                "error": {"code": "NOT_FOUND", "message": "Slot template not found"}
            }

        await db.commit()
        return {
            "ok": True,
            "data": {"message": "Slot template deactivated"},
            "error": None
        }
    except Exception as e:
        await db.rollback()
        return {
            "ok": False,
            "data": None,
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }
