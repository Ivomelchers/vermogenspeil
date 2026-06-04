from django.db import models


class MappingSource(models.TextChoices):
    SEED_JSON = "seed_json", "Seed (JSON)"
    OPENFIGI = "openfigi", "OpenFIGI"
    MANUAL = "manual", "Handmatig"


class InstrumentMapping(models.Model):
    """
    Globale ISIN → Yahoo-ticker (alle brokers, alle gebruikers).
    """

    isin = models.CharField("ISIN", max_length=12, primary_key=True)
    yahoo_ticker = models.CharField("Yahoo-ticker", max_length=32)
    mic = models.CharField("MIC", max_length=12, blank=True, default="")
    asset_type = models.CharField(
        "assettype-hint",
        max_length=20,
        blank=True,
        default="",
        help_text="stock, etf, fund — optioneel uit OpenFIGI",
    )
    security_type = models.CharField("OpenFIGI type", max_length=64, blank=True, default="")
    source = models.CharField(
        max_length=20,
        choices=MappingSource.choices,
        default=MappingSource.SEED_JSON,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "instrumentmapping"
        verbose_name_plural = "instrumentmappings"
        ordering = ["isin"]

    def __str__(self) -> str:
        return f"{self.isin} → {self.yahoo_ticker}"
