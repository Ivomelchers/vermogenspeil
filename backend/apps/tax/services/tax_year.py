"""Relevant belastingjaar — hoofdstuk 11 (Europe/Amsterdam, deadline 1 mei)."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


def relevant_tax_year(*, at: datetime | date | None = None) -> int:
    """
    Vóór 1 mei: vorig kalenderjaar. Vanaf 1 mei: lopend kalenderjaar.
    """
    if at is None:
        now = datetime.now(tz=AMSTERDAM)
    elif isinstance(at, date) and not isinstance(at, datetime):
        now = datetime(at.year, at.month, at.day, 12, 0, 0, tzinfo=AMSTERDAM)
    else:
        now = at.astimezone(AMSTERDAM) if at.tzinfo else at.replace(tzinfo=AMSTERDAM)

    year = now.year
    deadline = datetime(year, 5, 1, 0, 0, 0, tzinfo=AMSTERDAM)
    if now < deadline:
        return year - 1
    return year


def peildatum_date_for_year(tax_year: int) -> date:
    return date(tax_year, 1, 1)


def tax_year_context(*, at: datetime | date | None = None) -> dict:
    relevant = relevant_tax_year(at=at)
    if at is None:
        now = datetime.now(tz=AMSTERDAM)
    elif isinstance(at, date) and not isinstance(at, datetime):
        now = datetime(at.year, at.month, at.day, tzinfo=AMSTERDAM)
    else:
        now = at.astimezone(AMSTERDAM) if at.tzinfo else at.replace(tzinfo=AMSTERDAM)

    deadline = datetime(now.year, 5, 1, 0, 0, 0, tzinfo=AMSTERDAM)
    switched = now >= deadline

    return {
        "relevant_tax_year": relevant,
        "peildatum": peildatum_date_for_year(relevant).isoformat(),
        "timezone": "Europe/Amsterdam",
        "switched_on_may_first": switched,
        "rule": (
            f"Vanaf 1 mei {now.year} tonen we belastingjaar {relevant}."
            if switched
            else f"Vóór 1 mei {now.year} tonen we nog belastingjaar {relevant} (aangifte-voorbereiding)."
        ),
    }
