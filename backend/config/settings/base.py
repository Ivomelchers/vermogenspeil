"""Django settings — shared base configuration."""

import os
from pathlib import Path

import dj_database_url
from celery.schedules import crontab
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-change-me-in-production")

DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.portfolio",
    "apps.integrations",
    "apps.tax",
    "apps.pricing",
    "apps.payments",
    "apps.snapshots",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=False,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "nl-nl"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.Auth0Authentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET", "")
AUTH0_FRONTEND_CLIENT_ID = os.environ.get(
    "AUTH0_FRONTEND_CLIENT_ID",
    os.environ.get("VITE_AUTH0_CLIENT_ID", ""),
)
PASSWORD_RESET_TOKEN_HOURS = int(os.environ.get("PASSWORD_RESET_TOKEN_HOURS", "1"))
AUTH0_CONNECTION = os.environ.get("AUTH0_CONNECTION", "Username-Password-Authentication")

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "socket_connect_timeout": 2,
            "socket_timeout": 2,
        },
    }
}

# Koers-cache: live 5 min (env override); historisch 24 uur
PRICE_CACHE_TTL_LIVE_SECONDS = int(
    os.environ.get("PRICE_CACHE_TTL_LIVE_SECONDS", str(5 * 60))
)
PRICE_CACHE_TTL_HISTORICAL_SECONDS = 24 * 60 * 60
COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY", "")
OPENFIGI_ENABLED = os.environ.get("OPENFIGI_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)
OPENFIGI_API_KEY = os.environ.get("OPENFIGI_API_KEY", "")
INSTRUMENT_RESOLVE_MAX_PER_IMPORT = int(
    os.environ.get("INSTRUMENT_RESOLVE_MAX_PER_IMPORT", "15")
)
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    "annual-peildatum-snapshot": {
        "task": "apps.snapshots.tasks.run_annual_peildatum_snapshots",
        "schedule": crontab(minute=0, hour=0, day_of_month=1, month_of_year=1),
    },
    "refresh-live-prices": {
        "task": "apps.pricing.tasks.refresh_live_prices",
        "schedule": crontab(minute="*/5"),
    },
    "refresh-symbol-cache": {
        "task": "apps.pricing.tasks.refresh_symbol_cache",
        "schedule": crontab(minute=0, hour=2),  # 2 AM daily
    },
}

CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "").lower() in (
    "true",
    "1",
    "yes",
)
CELERY_TASK_EAGER_PROPAGATES = True

# Memory optimizations for resource-constrained environments
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Don't prefetch tasks into memory
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Recycle workers to free memory
CELERY_TASK_ACKS_LATE = True  # Acknowledge tasks after completion
CELERY_TASK_REJECT_ON_WORKER_LOST = True  # Re-queue if worker dies

# Task timeout configuration (prevents hanging tasks)
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 540  # 9 minutes soft limit (allows graceful shutdown)
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 minute between retries

DEMO_FEATURES_ENABLED = os.environ.get("DEMO_FEATURES_ENABLED", "").lower() in (
    "true",
    "1",
    "yes",
)

# Pre-launch: iedereen Premium-features (werkelijk rendement). Zet PREMIUM_UNLOCKED_FOR_ALL=false bij livegang.
PREMIUM_UNLOCKED_FOR_ALL = os.environ.get("PREMIUM_UNLOCKED_FOR_ALL", "true").lower() in (
    "true",
    "1",
    "yes",
)

# CSV-kolommapping: fallback als vaste aliases/fuzzy niet volstaan.
# Standaard AAN wanneer OPENAI_API_KEY gezet is; uitzetten met CSV_AI_COLUMN_MAPPING=false
_csv_ai_flag = os.environ.get("CSV_AI_COLUMN_MAPPING", "").strip().lower()
if _csv_ai_flag:
    CSV_AI_COLUMN_MAPPING = _csv_ai_flag in ("true", "1", "yes")
else:
    CSV_AI_COLUMN_MAPPING = bool(os.environ.get("OPENAI_API_KEY", ""))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
CSV_AI_COLUMN_MODEL = os.environ.get("CSV_AI_COLUMN_MODEL", "gpt-4o-mini")
_csv_ai_desc = os.environ.get("CSV_AI_DESCRIPTION_CLASSIFICATION", "").strip().lower()
if _csv_ai_desc:
    CSV_AI_DESCRIPTION_CLASSIFICATION = _csv_ai_desc in ("true", "1", "yes")
else:
    CSV_AI_DESCRIPTION_CLASSIFICATION = bool(os.environ.get("OPENAI_API_KEY", ""))

# Gedeelde CSV-kolomaliases: min. distinct users vóór alias voor iedereen geldt (default 2)
LEARNED_ALIAS_GLOBAL_MIN_USERS = int(os.environ.get("LEARNED_ALIAS_GLOBAL_MIN_USERS", "2"))
# date/total vereisen extra bevestigingen vóór gedeelde verify (default 3)
LEARNED_ALIAS_CRITICAL_MIN_USERS = int(os.environ.get("LEARNED_ALIAS_CRITICAL_MIN_USERS", "3"))

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")
MOLLIE_API_KEY = os.environ.get("MOLLIE_API_KEY", "")
BITVAVO_API_URL = os.environ.get("BITVAVO_API_URL", "https://api.bitvavo.com/v2")
BITVAVO_ACCESS_WINDOW = int(os.environ.get("BITVAVO_ACCESS_WINDOW", "10000"))
BYBIT_API_URL = os.environ.get("BYBIT_API_URL", "https://api.bybit.com")
BYBIT_RECV_WINDOW = int(os.environ.get("BYBIT_RECV_WINDOW", "5000"))
OKX_API_URL = os.environ.get("OKX_API_URL", "https://www.okx.com")
PRICE_API_KEY = os.environ.get("PRICE_API_KEY", "")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@mijnvermogen.nl")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")

if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# API Timeout Configuration
OKX_API_TIMEOUT = int(os.environ.get("OKX_API_TIMEOUT", "30"))
AUTH0_TIMEOUT = int(os.environ.get("AUTH0_TIMEOUT", "10"))
EXTERNAL_API_TIMEOUT = int(os.environ.get("EXTERNAL_API_TIMEOUT", "30"))
