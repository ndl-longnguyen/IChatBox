#!/usr/bin/env sh
set -eu

cd /app

python manage.py migrate --noinput

# Optional: collectstatic for prod-like runs (kept off by default)
if [ "${COLLECTSTATIC:-0}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

exec daphne -b 0.0.0.0 -p "${PORT:-8002}" core.asgi:application
