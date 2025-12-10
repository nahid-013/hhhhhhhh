#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "postgres" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is ready!"

echo "Running Alembic migrations..."
cd /app/backend
alembic upgrade head

echo "Migrations completed!"
cd /app

# Запускаем команду, переданную в docker-compose (uvicorn или celery)
exec "$@"
