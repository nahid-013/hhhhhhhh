"""
API эндпоинты для авторизации
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.schemas.auth import LoginRequest, LoginResponse
from backend.schemas.user import UserCreate
from backend.db.repository import user as user_repo
from backend.db.repository import slot as slot_repo
from backend.core.security import (
    create_access_token,
    validate_telegram_auth,
    generate_referral_code,
)
import json
from urllib.parse import unquote

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Авторизация через Telegram Mini App

    Проверяет подпись Telegram, создает или получает пользователя,
    возвращает JWT токен
    """
    # Валидация Telegram данных
    try:
        telegram_data = validate_telegram_auth(request.init_data)
    except HTTPException as e:
        return {
            "ok": False,
            "data": None,
            "error": {"code": "UNAUTHORIZED", "message": str(e.detail)},
        }

    # Извлекаем данные пользователя из telegram_data
    try:
        # Парсим user данные из init_data
        user_json = telegram_data.get("user")
        if user_json:
            user_data = json.loads(unquote(user_json))
            tg_id = user_data.get("id")
            username = user_data.get("username")
            first_name = user_data.get("first_name")
            last_name = user_data.get("last_name")
            language_code = user_data.get("language_code")
        else:
            raise ValueError("No user data in init_data")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user data: {str(e)}",
        )

    # Проверяем, существует ли пользователь
    user = await user_repo.get_user_by_tg_id(db, tg_id)
    is_new_user = False

    if not user:
        # Создаем нового пользователя
        is_new_user = True

        # Генерируем реферальный код
        referral_code = generate_referral_code(tg_id)

        # Проверяем реферальный код, если передан
        referrer_id = None
        if request.referral_code:
            referrer = await user_repo.get_user_by_referral_code(db, request.referral_code)
            if referrer:
                referrer_id = referrer.tg_id

        # Создаем пользователя
        user_create = UserCreate(
            tg_id=tg_id,
            user_name=username,
            first_name=first_name,
            last_name=last_name,
            language=language_code,
            referral_code=referral_code,
            referraled_by=referrer_id,
        )
        user = await user_repo.create_user(db, user_create)

        # Создаем стартовые слоты для нового пользователя
        await slot_repo.create_starter_slots_for_user(db, user.tg_id)
        await db.commit()

    # Создаем JWT токен
    access_token = create_access_token(
        data={"sub": user.tg_id, "username": user.user_name}
    )

    return {
        "ok": True,
        "data": LoginResponse(
            access_token=access_token,
            token_type="bearer",
            is_new_user=is_new_user,
        ),
        "error": None,
    }
