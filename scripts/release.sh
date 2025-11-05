#!/usr/bin/env bash
set -euo pipefail

echo "[release] Applying migrations..."
python manage.py migrate --noinput

echo "[release] Collecting static files..."
python manage.py collectstatic --noinput

echo "[release] Done."

