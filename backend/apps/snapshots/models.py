from django.conf import settings
from django.db import models


class PeilDatumSnapshot(models.Model):
    """
    Immutable vastlegging vermogen op 1 januari 00:00 CET (belastingpeildatum).
    TRAP 2: geen update of delete na creatie.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="peildatum_snapshots",
    )
    year = models.PositiveIntegerField("belastingjaar / peildatum-jaar")
    data = models.JSONField("snapshot payload")
    created_at = models.DateTimeField(auto_now_add=True)

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

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("PeilDatumSnapshot is immutable en kan niet worden gewijzigd.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("PeilDatumSnapshot is immutable en kan niet worden verwijderd.")

    def __str__(self):
        return f"Peildatum {self.year} (user {self.user_id})"
