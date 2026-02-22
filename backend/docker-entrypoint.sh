#!/bin/bash

set -e

echo "Starting GYM Club Backend..."

echo "Waiting for database to be ready..."

until pg_isready -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB}; do
  echo "Database is unavailable - sleeping..."
  sleep 2
done

echo "Database is ready!"

echo "Applying database migrations..."

alembic upgrade head

echo "Migrations applied successfully!"

echo "Starting FastAPI application..."

exec uvicorn src.main:app --host 0.0.0.0 --port 8000