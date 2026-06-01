from django.conf import settings
from django.db import models

from apps.snapshots.lock import is_peildatum_snapshot_locked


class PeilDatumSnapshot(models.Model):
    """
    Vastlegging vermogen op 1 januari 00:00 CET (belastingpeildatum).
    Herberekenbaar tot 1 mei van het volgende jaar (FSD §21.2.2); daarna locked.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="peildatum_snapshots",
    )
    year = models.PositiveIntegerField("belastingjaar / peildatum-jaar")
    data = models.JSONField("snapshot payload")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "peildatum-snapshot"
        verbose_name_plural = "peildatum-snapshots"
        ordering = ["-year"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "year"],
                name="unique_peildatum_snapshot_per_user_year",
            ),
        ]

    @property
    def is_locked(self) -> bool:
        return is_peildatum_snapshot_locked(self.year)

    def save(self, *args, **kwargs):
        if self.pk:
            if is_peildatum_snapshot_locked(self.year):
                raise ValueError(
                    f"Peildatum-snapshot {self.year} is vastgezet en kan niet worden gewijzigd."
                )
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                allowed = {"data", "updated_at"}
                if not set(update_fields).issubset(allowed):
                    raise ValueError("Alleen snapshot-data mag worden bijgewerkt.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("PeilDatumSnapshot kan niet worden verwijderd.")

    def __str__(self):
        return f"Peildatum {self.year} (user {self.user_id})"
