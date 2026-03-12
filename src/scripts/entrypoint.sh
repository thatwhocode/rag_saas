#!/bin/bash
set -e

echo "PostgreSQL is ready (checked by Docker) - checking migrations"

VERSIONS_DIR="/app/src/migrations/versions"

if ! ls $VERSIONS_DIR/*.py 1> /dev/null 2>&1; then
    echo "⚠️ Файлів міграцій не знайдено! Генерую першу міграцію..."
    alembic revision --autogenerate -m "initial_tables"
    echo "✅ Міграцію згенеровано."
else
    echo "ℹ️ Міграції вже існують, пропускаю генерацію."
fi

echo "🚀 Накочую міграції на базу..."
alembic -c /app/src/alembic.ini upgrade head

echo "Migrations completed - starting FastAPI"

exec "$@"