#!/usr/bin/env bash
set -euo pipefail

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Render free tier: geen aparte worker-service. Start Celery in deze container.
if [[ "${RUN_CELERY_IN_WEB:-}" == "true" ]]; then
  echo "RUN_CELERY_IN_WEB=true — starting Celery worker + beat in background"
  mkdir -p /tmp/celery
  celery -A config worker \
    --loglevel="${CELERY_LOG_LEVEL:-warning}" \
    --concurrency="${CELERY_CONCURRENCY:-1}" \
    --pool=solo \
    --detach \
    --pidfile=/tmp/celery/worker.pid \
    --logfile=/tmp/celery/worker.log
  celery -A config beat \
    --loglevel="${CELERY_LOG_LEVEL:-warning}" \
    --detach \
    --pidfile=/tmp/celery/beat.pid \
    --logfile=/tmp/celery/beat.log
fi

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --worker-class gevent \
  --workers "${WEB_CONCURRENCY:-1}" \
  --worker-connections 1000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
