# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Обзор проекта

HUNT — Web3 Telegram Mini App на TON blockchain. Игра где игроки собирают, развивают, скрещивают и торгуют NFT существами (Спиритами). Проект использует FastAPI, PostgreSQL, Redis, Celery, и TON SDK.

## Архитектура

### Backend Services (FastAPI async)
- **Auth & Profile Service** - Telegram авторизация, профили, рефералы, кошельки
- **Game Service** - Спириты, слоты, бусты, капсулы, breeding
- **Matchmaking & Battle Service** - PvP матчмейкинг, детерминированные бои (3 игрока)
- **Economy & Payments Service** - TON интеграция, Lumens (внутриигровая валюта)
- **NFT Service** - Минтинг, трансфер, burn NFT на TON
- **Admin Service** - CRUD, аналитика, управление drop rates
- **Worker Cluster** - Celery фоновые задачи (энергия, капсулы, выплаты)

### Инфраструктура
- **Database**: PostgreSQL с async SQLAlchemy + Alembic миграции
- **Cache**: Redis (кеш, лидерборды, матчмейкинг очереди, rate limiting)
- **Workers**: Celery + Redis broker
- **Storage**: S3-совместимое хранилище (аватары, спрайты, анимации)
- **Monitoring**: Prometheus + Grafana
- **Frontend**: Telegram Mini App (HTML5/TS, React/Vite)

## Команды разработки

### Запуск проекта
```bash
# Запуск всех сервисов (backend, postgres, redis, celery)
make up

# Остановка всех сервисов
make down

# Перезапуск
make restart
```

### База данных
```bash
# Создание новой миграции
make migration msg="описание миграции"

# Применение миграций
make migrate

# Откат последней миграции
make downgrade

# Создание начальных данных (elements, rarities, templates)
make seed
```

### Тестирование
```bash
# Запуск всех тестов
make test

# Запуск конкретного теста
make test-file path=tests/test_breeding.py

# Запуск с покрытием
make test-coverage
```

### Разработка
```bash
# Форматирование кода
make format

# Линтинг
make lint

# Проверка типов
make typecheck

# Запуск dev сервера с hot reload
make dev

# Просмотр логов
make logs service=game_service
```

### Celery Workers
```bash
# Запуск Celery worker
make worker

# Запуск Celery beat (планировщик)
make beat

# Мониторинг задач
make flower
```

### Docker
```bash
# Пересборка образов
make build

# Очистка volumes
make clean
```

## Структура базы данных

### Основные таблицы

**users** - Игроки, балансы (TON, Lumens), рефералы, кошельки
**elements** - Стихии (fire, water, earth, air, light, dark)
**rarities** - Редкости (common, rare, epic, legendary, mythical)

### Игровые сущности

**spirits_template** - Шаблоны спиритов (базовые характеристики)
**player_spirits** - Спириты игроков (NFT, level, xp, energy, stats)
**capsule_template** - Шаблоны капсул (цены, время открытия)
**player_capsules** - Капсулы игроков
**slots_template** - Шаблоны слотов для партии
**player_slots** - Слоты игроков
**boost_template** - Шаблоны бустов опыта
**player_boosts** - Бусты игроков

### PvP система

**battle_sessions** - Сессии боев (3 игрока, deterministic simulation)
**battle_players** - Участники боев, статистика, награды

### Экономика

**balance_logs** - История изменений балансов
**withdrawals** - Вывод TON (pending/processing/completed)
**donations** - Донаты игроков

## Ключевая бизнес-логика

### Breeding (скрещивание)
- Родители: одинаковый element_id и spirit_template_id, оба level=10
- Стоимость: TON fee + burn parents
- Формулы:
  - `child_gen = min(parent1_gen, parent2_gen) + 1`
  - `child_stat = max(parent1_stat, parent2_stat, min_stat_for_generation[gen])`
  - `rarity = max(parent1_rarity, parent2_rarity)`
- Родители сжигаются (NFT burn если смитнчены)
- Минимальные статы по поколениям в todo.md:7.7

### Energy System
- Восстановление: +5 energy каждые 10 минут (Celery task)
- max_energy = base_max_energy + (generation * 5)
- Мгновенное восстановление за TON/Lumens (с rate limiting)
- Каждый бой расходует 15 energy

### Capsule Opening
- Если open_time_seconds = 0: мгновенное открытие
- Если > 0: устанавливается таймер, Celery task завершает открытие
- Fast open: оплата fast_open_cost для мгновенного открытия
- Drop logic: weighted random по spirits_template с учетом rarity ограничений

### Battle System
- 3 игрока матчмейкинг по power_score
- Детерминированная симуляция на сервере (seeded PRNG)
- 5 мини-игр: Flow Flight, Deep Dive, Rhythm Path, Jump Rush, Collecting Frenzy
- Награды: XP спиритам, Lumens, шанс на капсулу
- Replay сохраняется в battle_sessions.result_json

### NFT Integration
- player_spirits.is_minted флаг указывает на NFT статус
- player_spirits.nft_id хранит blockchain токен reference
- Mint: оплата TON fee -> вызов NFT Service -> обновление DB
- Burn: on-chain burn -> обновление DB
- Reconciliation job для синхронизации с blockchain

## API Endpoints

Все эндпоинты возвращают: `{"ok": bool, "data": {...}, "error": {...}}`

### Profile
- `GET /api/v1/profile` - профиль пользователя
- `PATCH /api/v1/profile` - обновление профиля
- `POST /api/v1/profile/wallet/connect` - подключение TON кошелька
- `POST /api/v1/profile/wallet/withdraw` - вывод TON

### Spirits
- `GET /api/v1/spirits/catalog` - каталог шаблонов
- `GET /api/v1/spirits/my` - спириты игрока
- `POST /api/v1/spirits/{id}/activate` - активация в слот
- `POST /api/v1/spirits/{id}/mint` - минт NFT
- `POST /api/v1/spirits/breed` - скрещивание

### Capsules
- `GET /api/v1/capsules/shop` - магазин капсул
- `POST /api/v1/capsules/buy` - покупка
- `POST /api/v1/capsules/{id}/open` - открытие
- `POST /api/v1/capsules/{id}/fast_open` - быстрое открытие

### Slots & Boosts
- `GET /api/v1/slots/templates` - шаблоны слотов
- `POST /api/v1/slots/buy` - покупка слота
- `GET /api/v1/boosts/shop` - магазин бустов
- `POST /api/v1/boosts/{id}/use` - использование буста

### Admin (требует is_admin=true)
- `GET /api/v1/admin/users` - управление пользователями
- `POST /api/v1/admin/users/{id}/ban` - бан
- `POST /api/v1/admin/spirits/drops` - настройка drop rates
- CRUD для всех templates

## Безопасность и Anti-fraud

### Обязательные проверки
1. **Wallet duplicates** - детекция мультиаккаунтов по кошелькам, IP, device fingerprint
2. **Rate limiting** - token bucket per user, строгие лимиты для финансовых операций
3. **Withdrawal delays** - задержка 24-72ч для новых/подозрительных аккаунтов
4. **Energy restore limits** - max N мгновенных восстановлений за 24ч
5. **Audit logs** - иммутабельные логи для mint, burn, withdraw, transfers

### Авторизация
- JWT + Telegram mini-app signed payload validation
- Header: `X-Tg-Signed` для проверки на backend
- RBAC для admin эндпоинтов (is_admin флаг)

## Celery Tasks

### Периодические (Celery Beat)
- `tick_energy` - каждые 10 минут, +5 energy всем спиритам (до max)
- `process_withdrawals` - batch обработка выводов TON
- `update_leaderboards` - обновление Redis leaderboards

### Отложенные
- `finish_capsule_opening` - завершение открытия капсулы по таймеру
- `apply_referral_rewards` - применение реферальных наград

## Формулы

```python
# Breeding generation
child_gen = min(parent1.generation, parent2.generation) + 1

# Breeding stats (для каждого стата)
MIN_STATS = {
    1: 1, 2: 3, 3: 5, 4: 8, 5: 10, 6: 12, 7: 15
}
child_stat = max(parent1_stat, parent2_stat, MIN_STATS[child_gen])

# Energy restore
energy = min(current_energy + 5, max_energy)
max_energy = base_max_energy + (generation * 5)

# Battle power score
power = sum(stat * weight for stat, weight in stats.items()) * rarity_factor + level_bonus

# XP to next level
xp_for_next = floor(100 * level ** 1.2)
```

## Рекомендации по коду

### Стиль
- Все комментарии и docstrings на **русском языке**
- Простой, читаемый код без излишней абстракции
- Pydantic модели для валидации request/response
- Async SQLAlchemy для всех DB операций
- Type hints обязательны

### Транзакции
```python
# Используйте SELECT FOR UPDATE для конкурентных операций
async with session.begin():
    user = await session.execute(
        select(User).where(User.tg_id == tg_id).with_for_update()
    )
    # ... изменения балансов, покупки, breeding
```

### Error Codes
Консистентные коды ошибок:
- `UNAUTHORIZED` - 401
- `NOT_FOUND` - 404
- `INVALID_INPUT` - 400
- `RATE_LIMITED` - 429
- `FRAUD_SUSPECTED` - 403
- `INSUFFICIENT_FUNDS` - 402
- `COMPATIBILITY_ERROR` - 400 (element mismatch)
- `ALREADY_OPENING` - 409

### Денежные значения
- Всегда используйте `Decimal` для TON и Lumens
- В JSON передавайте как строки для избежания float проблем
- Atomic операции через DB transactions

## Миграции (Alembic)

Порядок создания таблиц (из-за FK зависимостей):
1. elements, rarities
2. users, wallets, bans, donations
3. capsule_template, slots_template, boost_template
4. spirits_template (с FK на capsule_template)
5. player_slots
6. player_spirits (с FK на player_slots)
7. player_capsules, player_boosts
8. battle_sessions, battle_players
9. balance_logs, withdrawals

## Тестирование

### Приоритеты
1. Breeding logic (валидации, формулы, NFT burn)
2. Capsule opening (drop weights, timers, fast open)
3. Energy system (ticks, limits, instant restore)
4. Battle simulation (deterministic, rewards)
5. Anti-fraud (multiaccount, rate limits)
6. TON integration (mint, burn, withdrawals)

### Фикстуры
Используйте pytest fixtures для:
- Test DB с автоматическим rollback
- Test user с балансами
- Template data (elements, rarities, spirits)
- Mock TON SDK calls

## План разработки (8 спринтов по 2 недели)

1. **Sprint 0**: Infra, CI/CD, DB schema, FastAPI skeleton
2. **Sprint 1**: Auth, Users, Templates, Wallet connect, Referrals
3. **Sprint 2**: Capsules, Boosts, Shop endpoints
4. **Sprint 3**: Spirits, Slots, Inventory, Party management
5. **Sprint 4**: Energy system, Celery workers, Anti-fraud basics
6. **Sprint 5**: Breeding, NFT integration stub
7. **Sprint 6**: Matchmaking, Battle simulation
8. **Sprint 7**: TON SDK integration, Payments, Withdrawals
9. **Sprint 8**: Monitoring, Admin UI, Production hardening

## Полезные файлы

- `todo.md` - полная спецификация проекта (ER схемы, API endpoints, формулы)
- `.env.example` - переменные окружения
- `alembic/versions/` - миграции БД
- `docker-compose.yml` - локальная разработка
