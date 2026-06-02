from django.conf import settings
from django.db import models

from apps.portfolio.querysets import UserOwnedManager


class PlatformType(models.TextChoices):
    BITVAVO = "bitvavo", "Bitvavo"
    DEGIRO = "degiro", "DEGIRO"
    MANUAL = "manual", "Handmatig"


class ConnectionMethod(models.TextChoices):
    API = "api", "API"
    CSV = "csv", "CSV"
    MANUAL = "manual", "Handmatig"


class SyncStatus(models.TextChoices):
    PENDING = "pending", "In wachtrij"
    RUNNING = "running", "Bezig"
    SUCCESS = "success", "Geslaagd"
    ERROR = "error", "Fout"


class PlatformConnection(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="platform_connections",
    )
    portfolio = models.ForeignKey(
        "portfolio.Portfolio",
        on_delete=models.CASCADE,
        related_name="platform_connections",
    )
    platform = models.CharField(max_length=32, choices=PlatformType.choices)
    connection_method = models.CharField(
        max_length=16,
        choices=ConnectionMethod.choices,
        default=ConnectionMethod.API,
    )
    label = models.CharField("label", max_length=120, blank=True, default="")
    api_key_encrypted = models.TextField(blank=True, default="")
    api_secret_encrypted = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=SyncStatus.choices,
        default=SyncStatus.PENDING,
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(
        "demo-koppeling",
        default=False,
        help_text="Voorbeelddata zonder echte broker-API. Alleen in development.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserOwnedManager()

    class Meta:
        verbose_name = "platformkoppeling"
        verbose_name_plural = "platformkoppelingen"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "platform", "label"],
                name="unique_platform_connection_label",
            ),
        ]

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        if self.label:
            return self.label
        return self.get_platform_display()


class SyncJob(models.Model):
    connection = models.ForeignKey(
        PlatformConnection,
        on_delete=models.CASCADE,
        related_name="sync_jobs",
    )
    status = models.CharField(
        max_length=16,
        choices=SyncStatus.choices,
        default=SyncStatus.PENDING,
    )
    celery_task_id = models.CharField(max_length=255, blank=True, default="")
    positions_synced = models.PositiveIntegerField(default=0)
    transactions_synced = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "sync-taak"
        verbose_name_plural = "sync-taken"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sync {self.connection_id} ({self.status})"


class CsvImportEvent(models.TextChoices):
    PREVIEW = "preview", "Preview"
    IMPORT = "import", "Import"
    REJECTED = "rejected", "Afgewezen"


class CsvImportDiagnostic(models.Model):
    """Geanonimiseerde CSV-drift signalen voor onderhoud (geen ruwe CSV)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="csv_import_diagnostics",
    )
    platform = models.CharField(max_length=32)
    schema_version = models.CharField(max_length=64, blank=True, default="")
    event = models.CharField(max_length=16, choices=CsvImportEvent.choices)
    failure_reason = models.CharField(max_length=64, blank=True, default="")
    file_headers = models.JSONField(default=list)
    missing_canonical = models.JSONField(default=list)
    unmapped_headers = models.JSONField(default=list)
    unknown_descriptions = models.JSONField(default=list)
    schema_warnings = models.JSONField(default=list)
    suggested_aliases = models.JSONField(default=list)
    rows_in_file = models.PositiveIntegerField(default=0)
    rows_recognized = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CSV-import diagnostiek"
        verbose_name_plural = "CSV-import diagnostiek"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["platform", "created_at"]),
            models.Index(fields=["event", "created_at"]),
        ]

    def __str__(self):
        return f"{self.platform} {self.event} ({self.created_at:%Y-%m-%d})"
