#!/bin/bash
set -e

echo "Running database migrations..."
uv run alembic -c migration/alembic.ini upgrade head
echo "Database migrations completed."
