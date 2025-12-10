"""
HUNT - Web3 Telegram Mini App
Главная точка входа FastAPI приложения
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings

# Создание FastAPI приложения
app = FastAPI(
    title="HUNT API",
    description="Web3 Telegram Mini App на TON blockchain",
    version="0.1.0",
    debug=settings.APP_DEBUG,
)

# Настройка CORS для Telegram Mini App (включая ngrok если настроен)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_with_ngrok,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "ok": True,
        "data": {
            "message": "HUNT API",
            "version": "0.1.0",
            "environment": settings.APP_ENV,
        },
        "error": None,
    }


@app.get("/health")
async def health_check():
    """Health check эндпоинт"""
    data = {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "base_url": settings.base_url,
    }

    # Добавляем информацию о ngrok если он включен
    if settings.NGROK_ENABLED:
        data["ngrok"] = {
            "enabled": True,
            "url": settings.NGROK_URL,
        }

    return {
        "ok": True,
        "data": data,
        "error": None,
    }


# Подключение роутеров
from backend.apis.v1 import (
    route_auth,
    route_profile,
    route_capsule,
    route_boost,
    route_spirit,
    route_slot,
    route_matchmaking,
    route_battle,
    route_leaderboard,
    route_admin,
)

app.include_router(route_auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(route_profile.router, prefix="/api/v1", tags=["Profile"])
app.include_router(route_capsule.router, prefix="/api/v1", tags=["Capsules"])
app.include_router(route_boost.router, prefix="/api/v1", tags=["Boosts"])
app.include_router(route_spirit.router, prefix="/api/v1", tags=["Spirits"])
app.include_router(route_slot.router, prefix="/api/v1", tags=["Slots"])
app.include_router(route_matchmaking.router, prefix="/api/v1", tags=["Matchmaking"])
app.include_router(route_battle.router, prefix="/api/v1", tags=["Battles"])
app.include_router(route_leaderboard.router, prefix="/api/v1", tags=["Leaderboards"])
app.include_router(route_admin.router, prefix="/api/v1", tags=["Admin"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )
