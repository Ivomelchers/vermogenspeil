#!/usr/bin/env bash
set -euo pipefail

exec celery -A config beat --loglevel="${CELERY_LOG_LEVEL:-info}"
