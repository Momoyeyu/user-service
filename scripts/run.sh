#!/bin/bash
set -e

uv run uvicorn src.main:app --reload --host "${SERVER_HOST:-0.0.0.0}" --port "${SERVER_PORT:-8000}" --no-access-log
