from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import UserManager


def default_active_tax_year():
    return timezone.now().year


class SubscriptionTier(models.TextChoices):
    FREE = "free", "Gratis"
    PREMIUM = "premium", "Premium"


class User(AbstractUser):
    """Custom user — e-mail als login, profiel- en belastinginstellingen."""

    username = None
    email = models.EmailField("e-mailadres", unique=True)
    first_name = models.CharField("voornaam", max_length=150)
    last_name = models.CharField("achternaam", max_length=150, blank=True)

    email_verified = models.BooleanField("e-mail geverifieerd", default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)

    subscription_tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE,
    )

    active_tax_year = models.PositiveIntegerField(
        "actief belastingjaar",
        default=default_active_tax_year,
        help_text="Belastingjaar waarvoor fiscale berekeningen worden getoond.",
    )
    has_fiscal_partner = models.BooleanField(
        "fiscaal partner",
        default=False,
        help_text="Verdubbelt het heffingsvrije vermogen in box 3-berekeningen.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "gebruiker"
        verbose_name_plural = "gebruikers"
        ordering = ["email"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        parts = [self.first_name, self.last_name]
        return " ".join(part for part in parts if part).strip()

    @property
    def is_premium(self):
        return self.subscription_tier == SubscriptionTier.PREMIUM
