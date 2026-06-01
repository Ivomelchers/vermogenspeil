from django.conf import settings
from django.db import models


class Box3DebtType(models.TextChoices):
    CONSUMER = "consumer", "Consumptief"
    INVESTMENT = "investment", "Beleggingsfinanciering"
    MORTGAGE_SECOND_HOME = "mortgage_second_home", "Hypotheek 2e woning"
    NEGATIVE_BALANCE = "negative_balance", "Negatief banksaldo"
    OTHER = "other", "Overig"


class Box3RealEstateType(models.TextChoices):
    SECOND_HOME_NL = "second_home_nl", "2e woning NL"
    SECOND_HOME_ABROAD = "second_home_abroad", "2e woning buitenland"
    RENTAL_NL = "rental_nl", "Verhuurd NL"
    RENTAL_ABROAD = "rental_abroad", "Verhuurd buitenland"
    OTHER = "other", "Overig onroerend"


class BijtellingMethod(models.TextChoices):
    HUURWAARDE = "huurwaarde", "Economische huurwaarde"
    WOZ_VAST = "woz_vast", "Vast percentage WOZ"


class TaxYearParameter(models.Model):
    """Fiscale parameters per belastingjaar (niet hardcoden in berekening)."""

    year = models.PositiveIntegerField(unique=True)
    heffingsvrij_vermogen = models.DecimalField(max_digits=14, decimal_places=2)
    rendement_banktegoeden = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        help_text="PB, bijv. 0.0128",
    )
    rendement_overige_bezittingen = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        help_text="PO, bijv. 0.06",
    )
    rendement_schulden = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        help_text="PS, bijv. 0.027",
    )
    schuldendrempel = models.DecimalField(max_digits=14, decimal_places=2, help_text="SD")
    tarief_box3 = models.DecimalField(max_digits=8, decimal_places=6, help_text="T, bijv. 0.36")
    banktegoeden_definitief = models.BooleanField(default=False)
    schulden_definitief = models.BooleanField(default=False)
    published_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "belastingjaar-parameter"
        verbose_name_plural = "belastingjaar-parameters"
        ordering = ["-year"]

    def __str__(self):
        return f"Box 3 parameters {self.year}"


class Box3Debt(models.Model):
    """Box 3-schuld (handmatig) — hoofdstuk 8."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="box3_debts",
    )
    tax_year = models.PositiveIntegerField("belastingjaar")
    label = models.CharField(max_length=120)
    debt_type = models.CharField(
        max_length=32,
        choices=Box3DebtType.choices,
        default=Box3DebtType.OTHER,
    )
    outstanding_eur = models.DecimalField(max_digits=14, decimal_places=2)
    interest_paid_ytd_eur = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Betaalde rente dit jaar (werkelijk rendement).",
    )
    creditor = models.CharField(max_length=120, blank=True, default="")
    linked_real_estate = models.ForeignKey(
        "Box3RealEstate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="debts",
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "box 3-schuld"
        verbose_name_plural = "box 3-schulden"
        ordering = ["-tax_year", "label"]

    def __str__(self):
        return f"{self.label} ({self.tax_year})"


class Box3RealEstate(models.Model):
    """Vastgoed in box 3 (handmatig) — hoofdstuk 9."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="box3_real_estate",
    )
    tax_year = models.PositiveIntegerField("belastingjaar")
    label = models.CharField(max_length=120)
    property_type = models.CharField(
        max_length=32,
        choices=Box3RealEstateType.choices,
        default=Box3RealEstateType.SECOND_HOME_NL,
    )
    value_eur = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="WOZ of WEV op peildatum",
    )
    is_abroad = models.BooleanField(default=False)
    annual_rent_eur = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Jaarhuur (voor leegwaarderatio indicatie).",
    )
    vacancy_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Leegwaarderatio 0–1 voor verhuur.",
    )
    rental_income_ytd_eur = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    eigen_gebruik_days = models.PositiveIntegerField(default=0)
    verhuur_days = models.PositiveIntegerField(default=0)
    verbouw_days = models.PositiveIntegerField(default=0)
    bijtelling_method = models.CharField(
        max_length=16,
        choices=BijtellingMethod.choices,
        blank=True,
        default="",
    )
    economic_rent_yearly_eur = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    woz_previous_year_eur = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="WOZ vorig jaar (methode B bijtelling).",
    )
    bijtelling_rate = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0,
        help_text="Leeg = standaard 5,06% voor 2026.",
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "box 3-vastgoed"
        verbose_name_plural = "box 3-vastgoed"
        ordering = ["-tax_year", "label"]

    def __str__(self):
        return f"{self.label} ({self.tax_year})"


class Box3BankAccountType(models.TextChoices):
    SAVINGS = "savings", "Spaarrekening"
    CHECKING = "checking", "Betaalrekening"
    DEPOSIT = "deposit", "Depositorekening"
    OTHER = "other", "Overig banktegoed"


class Box3BankBalance(models.Model):
    """Handmatig banktegoed (Box 3 categorie B)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="box3_bank_balances",
    )
    tax_year = models.PositiveIntegerField("belastingjaar")
    label = models.CharField(max_length=120)
    account_type = models.CharField(
        max_length=32,
        choices=Box3BankAccountType.choices,
        default=Box3BankAccountType.SAVINGS,
    )
    balance_eur = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Saldo op peildatum (1 januari).",
    )
    institution = models.CharField(max_length=120, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "box 3-banktegoed"
        verbose_name_plural = "box 3-banktegoeden"
        ordering = ["-tax_year", "label"]

    def __str__(self):
        return f"{self.label} ({self.tax_year})"
