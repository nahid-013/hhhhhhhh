# HUNT - Web3 Telegram Mini App

HUNT — это Web3 игра на TON blockchain, где игроки собирают, развивают, скрещивают и торгуют NFT существами (Спиритами).

## Технологический стек

### Backend
- **Framework**: FastAPI (async Python)
- **Database**: PostgreSQL с async SQLAlchemy
- **Cache**: Redis
- **Task Queue**: Celery + Redis broker
- **Migrations**: Alembic

### Blockchain
- **Network**: TON blockchain
- **NFT Standard**: ERC-721 style на TON

### DevOps
- **Containerization**: Docker + Docker Compose
- **Monitoring**: Prometheus + Grafana (планируется)

## Быстрый старт

### Требования
- Docker и Docker Compose
- Make (опционально, для удобных команд)

### Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd last_hunt
```

2. Создайте `.env` файл из примера:
```bash
make env
# или вручную
cp .env.example .env
```

3. Отредактируйте `.env` и установите необходимые переменные окружения

4. Запустите все сервисы:
```bash
make up
```

5. Примените миграции базы данных:
```bash
make migrate
```

6. API будет доступен на `http://localhost:8000`

## Разработка с ngrok (для Telegram Mini App)

Для тестирования Telegram Mini App необходим публичный HTTPS URL. Используйте ngrok для проброса локального сервера наружу.

### Быстрая настройка (рекомендуется)

1. Получите authtoken на [ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken)

2. Добавьте в `.env`:
```bash
NGROK_AUTH_TOKEN=your_token_here
```

3. Запустите ngrok:
```bash
./start_ngrok.sh
```

4. Скопируйте URL (например: `https://abc123.ngrok-free.app`) и обновите `.env`:
```bash
NGROK_ENABLED=true
NGROK_URL=https://abc123.ngrok-free.app
```

5. Перезапустите:
```bash
make restart
```

**Готово!** API доступен по ngrok URL, CORS настроен автоматически.

### С Docker Compose (опционально)

В `docker-compose.yml` есть закомментированный ngrok сервис. Раскомментируйте его и запустите:

```bash
# Раскомментируйте ngrok сервис в docker-compose.yml
# Затем запустите:
docker-compose --profile ngrok up

# Или просто:
make up
```

Web UI ngrok: http://localhost:4040

### Проверка

```bash
curl https://your-ngrok-url/health
```

Должен вернуться JSON с `"ngrok": {"enabled": true}`

**Подробная инструкция**: см. [NGROK_SETUP.md](NGROK_SETUP.md)

## Доступные команды

### Docker
- `make up` - Запустить все сервисы
- `make down` - Остановить все сервисы
- `make restart` - Перезапустить все сервисы
- `make build` - Пересобрать Docker образы
- `make clean` - Очистить volumes
- `make logs` - Просмотр логов всех сервисов
- `make logs service=backend` - Просмотр логов конкретного сервиса

### База данных
- `make migrate` - Применить миграции
- `make migration msg="описание"` - Создать новую миграцию
- `make downgrade` - Откатить последнюю миграцию
- `make seed` - Загрузить начальные данные

### Разработка
- `make dev` - Запустить dev сервер с hot reload
- `make format` - Форматирование кода (black, isort)
- `make lint` - Линтинг кода (flake8, pylint)
- `make typecheck` - Проверка типов (mypy)

### Тестирование
- `make test` - Запустить все тесты
- `make test-file path=tests/test_breeding.py` - Запустить конкретный тест
- `make test-coverage` - Запустить тесты с покрытием

### Celery
- `make worker` - Запустить Celery worker
- `make beat` - Запустить Celery beat (планировщик)
- `make flower` - Мониторинг Celery (доступен на http://localhost:5555)

### Утилиты
- `make shell` - Открыть shell в backend контейнере
- `make psql` - Подключиться к PostgreSQL
- `make redis-cli` - Подключиться к Redis
- `make help` - Показать все доступные команды

## Структура проекта

```
.
├── backend/                # FastAPI приложение
│   ├── apis/              # API endpoints
│   │   ├── v1/           # API версия 1
│   │   └── business_logic/
│   ├── core/             # Конфигурация и безопасность
│   ├── db/               # Модели и репозитории
│   │   ├── models/
│   │   └── repository/
│   ├── schemas/          # Pydantic схемы
│   ├── migrations/       # Alembic миграции
│   └── tests/            # Тесты
├── workers/              # Celery задачи
│   └── tasks/
├── frontend/             # Telegram Mini App (React)
├── infra/                # Инфраструктура
│   ├── docker/          # Dockerfiles
│   └── nginx/           # Nginx конфигурация
├── docs/                 # Документация
├── docker-compose.yml    # Docker Compose конфигурация
├── Makefile             # Команды для разработки
└── README.md            # Этот файл
```

## API Документация

После запуска приложения, Swagger UI доступен по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Разработка

### Создание новой миграции

```bash
make migration msg="add user table"
```

### Применение миграций

```bash
make migrate
```

### Запуск тестов

```bash
make test
```

### Форматирование и линтинг

```bash
make format
make lint
```

## Дополнительная документация

- [CLAUDE.md](CLAUDE.md) - Руководство по работе с проектом
- [ROADMAP.md](ROADMAP.md) - План разработки по спринтам
- [todo.md](todo.md) - Полная спецификация проекта

## Текущий статус

**Sprint 0 - COMPLETED** ✅
- Базовая инфраструктура настроена
- Docker Compose готов к использованию
- FastAPI приложение инициализировано
- Alembic настроен для миграций
- Makefile с командами создан

**Следующий этап: Sprint 1** - Базовые модели и авторизация

## Лицензия

[Указать лицензию]
# hhhhhhhh
