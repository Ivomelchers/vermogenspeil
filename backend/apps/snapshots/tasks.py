import logging

from celery import shared_task
from django.utils import timezone

from apps.snapshots.services.peildatum import create_peildatum_snapshots_for_all_users

logger = logging.getLogger(__name__)


@shared_task
def run_annual_peildatum_snapshots():
    """
    Jaarlijkse taak: 1 januari 00:00 Europe/Amsterdam (via Celery beat + CELERY_TIMEZONE).
    """
    year = timezone.now().year
    result = create_peildatum_snapshots_for_all_users(year)
    logger.info("Peildatum snapshots %s: %s", year, result)
    return result
