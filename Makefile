.PHONY: help up up-ngrok up-fast down restart build clean logs dev format lint typecheck test test-file test-coverage migrate migration downgrade seed worker beat flower

# Цвета для вывода
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## Показать справку по командам
	@echo "${BLUE}HUNT - Доступные команды:${NC}"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  ${BLUE}%-20s${NC} %s\n", $$1, $$2}'

# Docker команды
up: ## Запустить все сервисы
	@echo "${BLUE}Запуск всех сервисов...${NC}"
	docker-compose up -d
	@echo "${BLUE}Сервисы запущены. Backend доступен на http://localhost:8000${NC}"

up-ngrok: ## Запустить все сервисы с ngrok туннелем
	@echo "${BLUE}Запуск всех сервисов с ngrok...${NC}"
	docker-compose --profile ngrok up -d
	@echo "${BLUE}Сервисы запущены с ngrok${NC}"
	@echo "${BLUE}Ngrok Web UI доступен на http://localhost:4040${NC}"
	@echo "${BLUE}Проверьте публичный URL в Web UI${NC}"

up-fast: ## БЫСТРЫЙ запуск БЕЗ сборки образа (для разработки)
	@echo "${BLUE}Быстрый запуск без сборки образа...${NC}"
	@echo "${BLUE}Зависимости будут установлены при первом запуске контейнера${NC}"
	docker-compose -f docker-compose.dev.yml up -d
	@echo "${BLUE}Backend запущен на http://localhost:8000${NC}"

down: ## Остановить все сервисы
	@echo "${BLUE}Остановка всех сервисов...${NC}"
	docker-compose down
	docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

restart: ## Перезапустить все сервисы
	@echo "${BLUE}Перезапуск всех сервисов...${NC}"
	docker-compose restart

build: ## Быстрая пересборка с использованием кеша (рекомендуется)
	@echo "${BLUE}Быстрая пересборка с кешем и BuildKit...${NC}"
	DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose build

rebuild-clean: ## Полная пересборка без кеша (медленно, только при проблемах)
	@echo "${BLUE}Полная пересборка образов без кеша...${NC}"
	@echo "${BLUE}ВНИМАНИЕ: Это займет много времени!${NC}"
	DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose build --no-cache --parallel

rebuild-backend: ## Быстрая пересборка только backend (используйте после изменения requirements)
	@echo "${BLUE}Быстрая пересборка backend с кешем...${NC}"
	DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose build backend

clean: ## Очистить volumes
	@echo "${BLUE}Очистка volumes...${NC}"
	docker-compose down -v

logs: ## Просмотр логов (use: make logs service=backend)
	@if [ -z "$(service)" ]; then \
		docker-compose logs -f; \
	else \
		docker-compose logs -f $(service); \
	fi

# Database команды
migrate: ## Применить миграции
	@echo "${BLUE}Применение миграций...${NC}"
	docker-compose exec backend alembic upgrade head

migration: ## Создать новую миграцию (use: make migration msg="описание")
	@if [ -z "$(msg)" ]; then \
		echo "Использование: make migration msg=\"описание миграции\""; \
		exit 1; \
	fi
	@echo "${BLUE}Создание миграции: $(msg)${NC}"
	docker-compose exec backend alembic revision --autogenerate -m "$(msg)"

downgrade: ## Откатить последнюю миграцию
	@echo "${BLUE}Откат последней миграции...${NC}"
	docker-compose exec backend alembic downgrade -1

seed: ## Загрузить начальные данные
	@echo "${BLUE}Загрузка начальных данных...${NC}"
	docker-compose exec backend python -m backend.db.seed

# Development команды
dev: ## Запустить dev сервер с hot reload
	@echo "${BLUE}Запуск dev сервера...${NC}"
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

format: ## Форматирование кода (black, isort)
	@echo "${BLUE}Форматирование кода...${NC}"
	docker-compose exec backend black backend/ workers/
	docker-compose exec backend isort backend/ workers/

lint: ## Линтинг кода (flake8, pylint)
	@echo "${BLUE}Линтинг кода...${NC}"
	docker-compose exec backend flake8 backend/ workers/ --max-line-length=100 --exclude=__pycache__,migrations
	docker-compose exec backend pylint backend/ workers/ --disable=C0111,R0903

typecheck: ## Проверка типов (mypy)
	@echo "${BLUE}Проверка типов...${NC}"
	docker-compose exec backend mypy backend/ workers/ --ignore-missing-imports

# Testing команды
test: ## Запустить все тесты
	@echo "${BLUE}Запуск тестов...${NC}"
	docker-compose exec backend pytest backend/tests/ -v

test-file: ## Запустить конкретный тест (use: make test-file path=tests/test_breeding.py)
	@if [ -z "$(path)" ]; then \
		echo "Использование: make test-file path=tests/test_breeding.py"; \
		exit 1; \
	fi
	@echo "${BLUE}Запуск теста: $(path)${NC}"
	docker-compose exec backend pytest backend/$(path) -v

test-coverage: ## Запустить тесты с покрытием
	@echo "${BLUE}Запуск тестов с покрытием...${NC}"
	docker-compose exec backend pytest backend/tests/ --cov=backend --cov-report=html --cov-report=term

# Celery команды
worker: ## Запустить Celery worker
	@echo "${BLUE}Запуск Celery worker...${NC}"
	cd backend && celery -A workers.celery_app worker --loglevel=info

beat: ## Запустить Celery beat (планировщик)
	@echo "${BLUE}Запуск Celery beat...${NC}"
	cd backend && celery -A workers.celery_app beat --loglevel=info

flower: ## Запустить Flower (мониторинг Celery)
	@echo "${BLUE}Flower доступен на http://localhost:5555${NC}"
	@docker-compose logs -f flower

# Utility команды
shell: ## Открыть shell в backend контейнере
	docker-compose exec backend /bin/bash

psql: ## Подключиться к PostgreSQL
	docker-compose exec postgres psql -U hunt_user -d hunt_db

redis-cli: ## Подключиться к Redis
	docker-compose exec redis redis-cli

env: ## Создать .env из .env.example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "${BLUE}.env файл создан из .env.example${NC}"; \
	else \
		echo "${BLUE}.env файл уже существует${NC}"; \
	fi
