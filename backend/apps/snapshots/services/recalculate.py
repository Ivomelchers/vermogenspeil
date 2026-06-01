"""Peildatum-snapshot herberekening (FSD §21.2.2)."""

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.snapshots.lock import is_peildatum_snapshot_locked
from apps.snapshots.models import PeilDatumSnapshot
from apps.snapshots.services.peildatum import build_peildatum_payload, peildatum_instant_cet

logger = logging.getLogger(__name__)
AMSTERDAM = ZoneInfo("Europe/Amsterdam")


def transaction_affects_peildatum_year(occurred_at: datetime, year: int) -> bool:
    """Transactie telt mee voor peildatum 1 januari van `year`."""
    if timezone.is_naive(occurred_at):
        occurred_at = timezone.make_aware(occurred_at, AMSTERDAM)
    local_date = occurred_at.astimezone(AMSTERDAM).date()
    return local_date <= date(year, 1, 1)


def recalculate_peildatum_snapshot(snapshot: PeilDatumSnapshot) -> PeilDatumSnapshot:
    if is_peildatum_snapshot_locked(snapshot.year):
        raise ValueError(
            f"Peildatum-snapshot {snapshot.year} is vastgezet (na 1 mei). "
            "Herberekening is niet meer mogelijk."
        )

    payload = build_peildatum_payload(snapshot.user, snapshot.year)
    payload["recalculated_at"] = timezone.now().isoformat()
    payload["peildatum_instant"] = peildatum_instant_cet(snapshot.year).isoformat()
    snapshot.data = payload
    snapshot.save(update_fields=["data", "updated_at"])
    logger.info("Peildatum-snapshot %s herberekend voor user %s", snapshot.year, snapshot.user_id)
    return snapshot


def maybe_recalculate_peildatum_snapshots(user, occurred_at: datetime) -> list[dict]:
    """
    Herbereken ontgrendelde snapshots wanneer een transactie vóór/op peildatum valt.
    Retourneert lijst met {year, recalculated, locked_skipped}.
    """
    results: list[dict] = []
    for snapshot in PeilDatumSnapshot.objects.filter(user=user):
        year = snapshot.year
        if is_peildatum_snapshot_locked(year):
            if transaction_affects_peildatum_year(occurred_at, year):
                results.append(
                    {
                        "year": year,
                        "recalculated": False,
                        "locked": True,
                        "warning": (
                            f"Transactie valt onder peildatum {year}, maar die snapshot is "
                            "vastgezet na 1 mei. Wijziging telt niet meer mee in dat jaar."
                        ),
                    }
                )
            continue

        if not transaction_affects_peildatum_year(occurred_at, year):
            continue

        recalculate_peildatum_snapshot(snapshot)
        results.append({"year": year, "recalculated": True, "locked": False})

    return results
