#!/usr/bin/env bash
set -euo pipefail

exec celery -A config worker \
  --loglevel="${CELERY_LOG_LEVEL:-info}" \
  --concurrency="${CELERY_CONCURRENCY:-2}"
