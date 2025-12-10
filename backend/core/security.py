"""
Утилиты безопасности: JWT, Telegram auth
"""
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.core.config import settings
from backend.schemas.auth import TokenData

security = HTTPBearer()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Создание JWT токена
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Проверка и декодирование JWT токена
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        tg_id: int = payload.get("sub")
        if tg_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        token_data = TokenData(tg_id=tg_id, username=payload.get("username"))
        return token_data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """
    Dependency для получения tg_id текущего пользователя из JWT токена
    """
    token_data = verify_token(credentials.credentials)
    return token_data.tg_id


def validate_telegram_auth(init_data: str) -> Dict[str, Any]:
    """
    Валидация данных авторизации Telegram Mini App

    Проверяет подпись данных с помощью bot token
    Формат init_data: query string с параметрами от Telegram
    """
    try:
        # Парсинг init_data
        params = {}
        for item in init_data.split("&"):
            if "=" in item:
                key, value = item.split("=", 1)
                params[key] = value

        # Получаем hash из параметров
        received_hash = params.pop("hash", None)
        if not received_hash:
            raise ValueError("No hash in init_data")

        # Сортируем параметры и создаем data_check_string
        data_check_arr = [f"{k}={v}" for k, v in sorted(params.items())]
        data_check_string = "\n".join(data_check_arr)

        # Создаем secret_key из bot token
        secret_key = hmac.new(
            "WebAppData".encode(),
            settings.TELEGRAM_BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        # Проверяем hash
        if calculated_hash != received_hash:
            raise ValueError("Invalid hash")

        # Проверяем auth_date (не старше 24 часов)
        auth_date = int(params.get("auth_date", 0))
        current_time = int(datetime.utcnow().timestamp())
        if current_time - auth_date > 86400:  # 24 часа
            raise ValueError("Auth data is too old")

        return params

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Telegram authentication: {str(e)}",
        )


async def get_current_admin_user(
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Dependency для проверки прав администратора.

    Использование в admin эндпоинтах:
    ```python
    @router.post("/admin/something")
    async def admin_endpoint(
        admin_user_id: int = Depends(get_current_admin_user),
        db: AsyncSession = Depends(get_db)
    ):
        # Доступ разрешен только для админов
        # admin_user_id содержит tg_id админа
        ...
    ```

    Примечание: Эта функция только проверяет JWT токен и извлекает user_id.
    Для полной проверки is_admin в БД используйте verify_admin_access() внутри эндпоинта.

    Returns:
        int: tg_id текущего пользователя
    """
    return current_user_id


async def verify_admin_access(db, current_user_id: int):
    """
    Проверка прав администратора в БД

    Args:
        db: AsyncSession для работы с БД
        current_user_id: tg_id пользователя

    Raises:
        HTTPException 403: Если пользователь не админ

    Returns:
        User: Объект пользователя-администратора
    """
    from backend.db.repository import user as user_repo

    user = await user_repo.get_user_by_tg_id(db, current_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found"
        )

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return user


def generate_referral_code(tg_id: int) -> str:
    """
    Генерация уникального реферального кода на основе tg_id
    """
    # Используем простой алгоритм: базируемся на tg_id + salt
    code = hashlib.sha256(f"{tg_id}{settings.JWT_SECRET_KEY}".encode()).hexdigest()[:8].upper()
    return code
