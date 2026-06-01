from django.conf import settings
from django.db import models

from .querysets import UserOwnedManager


class VermogensCategorie(models.TextChoices):
    BANKTEGOED = "banktegoed", "Banktegoed"
    BELEGGING = "belegging", "Belegging"
    EDELMETAAL = "edelmetaal", "Edelmetaal"
    SCHULD = "schuld", "Schuld"
    OVERIG = "overig", "Overig"


class AssetType(models.TextChoices):
    CRYPTO = "crypto", "Crypto"
    STOCK = "stock", "Aandeel"
    ETF = "etf", "ETF"
    FUND = "fund", "Fonds"
    METAL = "metal", "Edelmetaal"
    CASH = "cash", "Spaargeld"
    OTHER = "other", "Overig"


class Portfolio(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="portfolios",
    )
    name = models.CharField("naam", max_length=120, default="Hoofdportefeuille")
    is_default = models.BooleanField("standaard", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserOwnedManager()

    class Meta:
        verbose_name = "portefeuille"
        verbose_name_plural = "portefeuilles"
        ordering = ["-is_default", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_default=True),
                name="unique_default_portfolio_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.user_id})"


class Asset(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assets",
    )
    symbol = models.CharField("symbool", max_length=32)
    name = models.CharField("naam", max_length=200, blank=True)
    asset_type = models.CharField(
        max_length=20,
        choices=AssetType.choices,
        default=AssetType.OTHER,
    )
    category = models.CharField(
        max_length=20,
        choices=VermogensCategorie.choices,
        default=VermogensCategorie.BELEGGING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserOwnedManager()

    class Meta:
        verbose_name = "asset"
        verbose_name_plural = "assets"
        ordering = ["symbol"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "symbol"],
                name="unique_asset_symbol_per_user",
            ),
        ]

    def __str__(self):
        return self.symbol


class Position(models.Model):
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="positions",
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="positions",
    )
    quantity = models.DecimalField(
        "aantal",
        max_digits=24,
        decimal_places=12,
        default=0,
    )
    average_cost_eur = models.DecimalField(
        "gemiddelde kostprijs (EUR)",
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "positie"
        verbose_name_plural = "posities"
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "asset"],
                name="unique_position_per_portfolio_asset",
            ),
        ]

    def __str__(self):
        return f"{self.asset.symbol} @ {self.portfolio_id}"


class TransactionType(models.TextChoices):
    BUY = "buy", "Aankoop"
    SELL = "sell", "Verkoop"
    DIVIDEND = "dividend", "Dividend"
    DEPOSIT = "deposit", "Storting"
    WITHDRAWAL = "withdrawal", "Opname"
    FEE = "fee", "Kosten"
    OTHER = "other", "Overig"


class Transaction(models.Model):
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )
    quantity = models.DecimalField(max_digits=24, decimal_places=12)
    price_eur = models.DecimalField(
        "prijs per eenheid (EUR)",
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
    )
    fee_eur = models.DecimalField(
        "kosten (EUR)",
        max_digits=18,
        decimal_places=6,
        default=0,
    )
    total_eur = models.DecimalField(
        "totaal (EUR)",
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
    )
    occurred_at = models.DateTimeField("datum")
    external_id = models.CharField(
        "extern ID",
        max_length=128,
        blank=True,
        default="",
    )
    transaction_hash = models.CharField(
        max_length=64,
        db_index=True,
    )
    source_platform = models.CharField(max_length=32, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "transactie"
        verbose_name_plural = "transacties"
        ordering = ["-occurred_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "transaction_hash"],
                name="unique_transaction_hash_per_portfolio",
            ),
        ]

    def __str__(self):
        return f"{self.transaction_type} {self.asset.symbol}"
