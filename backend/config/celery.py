import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("vermogenspeil")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Load task monitoring and error handling
from config import celery_monitoring  # noqa: F401, E402
