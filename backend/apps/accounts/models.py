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
    auth_0_id = models.CharField(
        "Auth0 user ID",
        max_length=128,
        unique=True,
        null=True,
        blank=True,
    )
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

    totp_secret_encrypted = models.TextField(
        "TOTP-geheim (versleuteld)",
        blank=True,
        default="",
    )
    is_2fa_enabled = models.BooleanField("2FA ingeschakeld", default=False)
    totp_confirmed_at = models.DateTimeField(null=True, blank=True)

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


class PasswordResetToken(models.Model):
    """Eenmalige gehashte token voor wachtwoord reset (Auth0 wachtwoord update)."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "wachtwoord-reset token"
        verbose_name_plural = "wachtwoord-reset tokens"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Wachtwoord reset voor {self.user.email}"


class MfaLoginChallenge(models.Model):
    """Tijdelijke challenge na wachtwoordlogin wanneer 2FA actief is."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mfa_login_challenges",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    tokens_encrypted = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "MFA-login challenge"
        verbose_name_plural = "MFA-login challenges"
        ordering = ["-created_at"]

    def __str__(self):
        return f"MFA challenge voor {self.user.email}"

    def is_valid(self):
        return self.used_at is None and timezone.now() < self.expires_at

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])


class TwoFactorBackupCode(models.Model):
    """Eenmalige backupcode voor 2FA."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="two_factor_backup_codes",
    )
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "2FA-backupcode"
        verbose_name_plural = "2FA-backupcodes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Backupcode voor {self.user.email}"
