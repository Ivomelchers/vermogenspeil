"""Peildatum-snapshot lock-datum (FSD §21.2.1)."""

from datetime import date

from django.utils import timezone
from zoneinfo import ZoneInfo

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


def peildatum_lock_date(year: int) -> date:
    return date(year + 1, 5, 1)


def is_peildatum_snapshot_locked(year: int, *, on_date: date | None = None) -> bool:
    on_date = on_date or timezone.now().astimezone(AMSTERDAM).date()
    return on_date >= peildatum_lock_date(year)
