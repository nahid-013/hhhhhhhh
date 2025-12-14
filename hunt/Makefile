.PHONY: help build up down restart logs ps clean dev dev-up dev-down migrate db-push

help:
	@echo "Доступные команды:"
	@echo "  make build     - Собрать образы"
	@echo "  make up        - Запустить сервисы (production)"
	@echo "  make down      - Остановить сервисы (production)"
	@echo "  make restart   - Перезапустить сервисы (production)"
	@echo "  make logs      - Показать логи"
	@echo "  make ps        - Показать статус контейнеров"
	@echo "  make clean     - Удалить контейнеры и volumes"
	@echo "  make migrate   - Применить миграции в контейнере"
	@echo "  make db-push   - Синхронизировать схему БД (без миграций)"
	@echo "  make dev       - Запустить в режиме разработки"
	@echo "  make dev-up    - Запустить только БД для разработки"
	@echo "  make dev-down  - Остановить БД для разработки"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v
	docker compose -f docker-compose.dev.yml down -v

dev:
	docker compose -f docker-compose.dev.yml up

dev-up:
	docker compose -f docker-compose.dev.yml up -d postgres

dev-down:
	docker compose -f docker-compose.dev.yml down

migrate:
	docker compose exec app npx prisma migrate deploy

db-push:
	docker compose exec app npx prisma db push

