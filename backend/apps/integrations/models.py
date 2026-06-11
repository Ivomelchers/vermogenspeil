from django.conf import settings
from django.db import models

from apps.portfolio.querysets import UserOwnedManager


class PlatformType(models.TextChoices):
    BITVAVO = "bitvavo", "Bitvavo"
    BYBIT = "bybit", "Bybit"
    OKX = "okx", "OKX"
    DEGIRO = "degiro", "DEGIRO"
    TRADING212 = "trading212", "Trading 212"
    TRADE_REPUBLIC = "trade_republic", "Trade Republic"
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


class OkxDomain(models.TextChoices):
    COM = "okx.com", "okx.com (Global - www.okx.com)"
    EEA = "eea.okx.com", "eea.okx.com (EU/NL - my.okx.com)"
    US = "us.okx.com", "us.okx.com (US/AU - app.okx.com)"


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
    api_passphrase_encrypted = models.TextField(blank=True, default="")
    okx_domain = models.CharField(
        max_length=16,
        choices=OkxDomain.choices,
        default=OkxDomain.COM,
        help_text="OKX API domein (okx.com of okx.nl)",
    )
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


class PlatformImportBatch(models.Model):
    """Eén CSV-upload of API-sync — groepeert geïmporteerde transacties."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="platform_import_batches",
    )
    connection = models.ForeignKey(
        PlatformConnection,
        on_delete=models.CASCADE,
        related_name="import_batches",
    )
    sync_job = models.ForeignKey(
        SyncJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_batches",
    )
    platform = models.CharField(max_length=32, choices=PlatformType.choices)
    connection_method = models.CharField(
        max_length=16,
        choices=ConnectionMethod.choices,
        default=ConnectionMethod.CSV,
    )
    source_label = models.CharField(max_length=160, blank=True, default="")
    source_filename = models.CharField(max_length=255, blank=True, default="")
    ai_used = models.BooleanField(default=False)
    column_mapping = models.JSONField(default=dict, blank=True)
    rows_in_file = models.PositiveIntegerField(default=0)
    rows_recognized = models.PositiveIntegerField(default=0)
    transactions_imported = models.PositiveIntegerField(default=0)
    transactions_skipped = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserOwnedManager()

    class Meta:
        verbose_name = "platform-import"
        verbose_name_plural = "platform-imports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["connection", "created_at"]),
            models.Index(fields=["platform", "created_at"]),
        ]

    def __str__(self):
        return f"{self.platform} import #{self.pk} ({self.created_at:%Y-%m-%d %H:%M})"


class LearnedAliasStatus(models.TextChoices):
    PENDING = "pending", "In afwachting"
    VERIFIED = "verified", "Geverifieerd"
    DISABLED = "disabled", "Uitgeschakeld"


class UserCsvColumnAlias(models.Model):
    """Persoonlijke kolomaliases — direct na geslaagde AI-import (alleen die user)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="csv_column_aliases",
    )
    platform = models.CharField(max_length=32, choices=PlatformType.choices)
    canonical = models.CharField(max_length=32)
    header_normalized = models.CharField(max_length=128)
    header_example = models.CharField(max_length=255, blank=True, default="")
    source_import_batch = models.ForeignKey(
        PlatformImportBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_column_aliases_created",
    )
    use_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "CSV-kolomalias (user)"
        verbose_name_plural = "CSV-kolomaliases (user)"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "platform", "header_normalized"],
                name="unique_user_csv_column_alias",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "platform"]),
            models.Index(fields=["platform", "header_normalized"]),
        ]

    def __str__(self):
        return f"{self.user_id}/{self.platform}: {self.header_normalized} → {self.canonical}"


class SharedCsvColumnAlias(models.Model):
    """Globale kolomaliases — pas actief voor iedereen na meerdere bevestigingen."""

    platform = models.CharField(max_length=32, choices=PlatformType.choices)
    canonical = models.CharField(max_length=32)
    header_normalized = models.CharField(max_length=128)
    header_example = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=LearnedAliasStatus.choices,
        default=LearnedAliasStatus.PENDING,
    )
    confirmation_count = models.PositiveIntegerField(default=0)
    conflict_count = models.PositiveIntegerField(default=0)
    first_import_batch = models.ForeignKey(
        PlatformImportBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shared_column_aliases_first",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "CSV-kolomalias (gedeeld)"
        verbose_name_plural = "CSV-kolomaliases (gedeeld)"
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "header_normalized"],
                name="unique_shared_csv_column_alias",
            ),
        ]
        indexes = [
            models.Index(fields=["platform", "status"]),
        ]

    def __str__(self):
        return f"{self.platform}: {self.header_normalized} → {self.canonical} ({self.status})"


class SharedCsvColumnAliasConfirmation(models.Model):
    """Welke users een gedeelde alias hebben bevestigd via geslaagde import."""

    alias = models.ForeignKey(
        SharedCsvColumnAlias,
        on_delete=models.CASCADE,
        related_name="confirmations",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shared_csv_alias_confirmations",
    )
    import_batch = models.ForeignKey(
        PlatformImportBatch,
        on_delete=models.CASCADE,
        related_name="shared_alias_confirmations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "CSV-kolomalias bevestiging"
        verbose_name_plural = "CSV-kolomalias bevestigingen"
        constraints = [
            models.UniqueConstraint(
                fields=["alias", "user"],
                name="unique_shared_csv_alias_confirmation",
            ),
        ]
