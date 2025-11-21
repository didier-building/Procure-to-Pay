#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # Exit on error

# Install UV if not available
if ! command -v uv &> /dev/null; then
    pip install uv
fi

# Install dependencies
uv sync

# Collect static files
uv run python manage.py collectstatic --noinput

# Run database migrations  
uv run python manage.py migrate