"""Celery task monitoring and error handling."""

import logging

from celery import signals

logger = logging.getLogger(__name__)


@signals.task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Log task failures for monitoring."""
    logger.error(
        f"Task {sender} (ID: {task_id}) failed with error: {exception}",
        exc_info=True,
        extra={"task_name": sender, "task_id": task_id},
    )


@signals.task_retry.connect
def handle_task_retry(sender=None, task_id=None, reason=None, **kwargs):
    """Log task retries."""
    logger.warning(
        f"Task {sender} (ID: {task_id}) retrying due to: {reason}",
        extra={"task_name": sender, "task_id": task_id},
    )


@signals.task_success.connect
def handle_task_success(sender=None, task_id=None, **kwargs):
    """Log successful task completion (debug level)."""
    logger.debug(
        f"Task {sender} (ID: {task_id}) completed successfully",
        extra={"task_name": sender, "task_id": task_id},
    )


@signals.task_prerun.connect
def handle_task_prerun(sender=None, task_id=None, **kwargs):
    """Log when task starts (debug level)."""
    logger.debug(
        f"Task {sender} (ID: {task_id}) starting",
        extra={"task_name": sender, "task_id": task_id},
    )
