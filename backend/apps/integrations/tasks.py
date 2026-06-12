from celery import shared_task
import logging

from apps.integrations.models import PlatformConnection, SyncJob
from apps.integrations.services.sync import run_connection_sync

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_platform_connection(self, sync_job_id: int):
    try:
        run_connection_sync(sync_job_id)
    except Exception as exc:
        raise self.retry(exc=exc) from exc


@shared_task(bind=True)
def sync_all_active_connections(self):
    """Scheduled task to sync all active platform connections (runs daily at 1 AM)."""
    active_connections = PlatformConnection.objects.filter(is_active=True)
    logger.info(f"[SYNC] Starting daily sync for {active_connections.count()} active connections")

    synced_count = 0
    for connection in active_connections:
        try:
            sync_job = SyncJob.objects.create(connection=connection, status="pending")
            sync_platform_connection.delay(sync_job.id)
            synced_count += 1
        except Exception as exc:
            logger.error(f"[SYNC] Error creating sync job for connection {connection.id}: {exc}")

    logger.info(f"[SYNC] Created {synced_count} sync jobs for daily auto-sync")
    return synced_count
