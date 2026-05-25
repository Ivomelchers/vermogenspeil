import secrets
from datetime import timedelta

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


class EmailVerificationToken(models.Model):
    """Eenmalige token voor e-mailverificatie (24 uur geldig)."""

    TOKEN_VALIDITY = timedelta(hours=24)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "e-mailverificatie-token"
        verbose_name_plural = "e-mailverificatie-tokens"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Verificatie voor {self.user.email}"

    @classmethod
    def create_for_user(cls, user):
        cls.objects.filter(user=user, used_at__isnull=True).update(
            used_at=timezone.now(),
        )
        return cls.objects.create(
            user=user,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + cls.TOKEN_VALIDITY,
        )

    def is_valid(self):
        return self.used_at is None and timezone.now() < self.expires_at

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
