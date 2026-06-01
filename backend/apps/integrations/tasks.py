from celery import shared_task

from apps.integrations.services.sync import run_connection_sync


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_platform_connection(self, sync_job_id: int):
    try:
        run_connection_sync(sync_job_id)
    except Exception as exc:
        raise self.retry(exc=exc) from exc
