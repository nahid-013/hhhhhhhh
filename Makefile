.PHONY: help build up down restart logs ps clean dev dev-up dev-down migrate db-push install


help: 
	@echo "Доступные команды:"
	@echo ""
	@echo "  Development:"

help:
	@echo "Доступные команды:"
	@echo ""
	@echo "  Development:"
	@echo "    make install     - Установить зависимости для всех сервисов"
	@echo "    make dev         - Запустить все сервисы в режиме разработки"
	@echo "    make dev-up      - Запустить только БД для разработки"
	@echo "    make dev-down    - Остановить dev окружение"
	@echo ""
	@echo "  Production:"
	@echo "    make build       - Собрать образы"
	@echo "    make up          - Запустить сервисы (production)"
	@echo "    make down        - Остановить сервисы (production)"
	@echo "    make restart     - Перезапустить сервисы (production)"

	
	@echo ""
	@echo "  Database:"
	@echo "    make migrate     - Применить миграции"
	@echo "    make db-push     - Синхронизировать схему БД"
	@echo ""
	@echo "  Utility:"
	@echo "    make logs        - Показать логи"
	@echo "    make ps          - Показать статус контейнеров"
	@echo "    make clean       - Удалить контейнеры и volumes"

install:
	cd hunt && npm install
	cd games && npm install

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
	cd hunt && npx prisma migrate deploy

db-push:
	cd hunt && npx prisma db push
