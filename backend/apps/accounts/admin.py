from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone

from .models import EmailLog, EmailVerificationToken, PasswordResetToken, User
from .services.email_service import send_email


def resend_verification_email(modeladmin, request, queryset):
    """Admin action: Send verification email to selected unverified users."""
    count = 0
    for user in queryset.filter(email_verified=False):
        token = EmailVerificationToken.create_for_user(user)
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
        try:
            send_email(
                user=user,
                email_type=EmailLog.EmailType.VERIFICATION,
                subject="Verify your email — Vermogenspeil",
                recipient=user.email,
                template_data={"verification_link": verification_link}
            )
            count += 1
        except Exception as e:
            messages.error(request, f"Failed to send to {user.email}: {str(e)}")
    messages.success(request, f"Sent {count} verification emails")


resend_verification_email.short_description = "Resend verification email to selected users"


def send_password_reset_email(modeladmin, request, queryset):
    """Admin action: Send password reset link to selected users."""
    count = 0
    for user in queryset:
        token = PasswordResetToken.objects.create(
            user=user,
            token=__import__('secrets').token_urlsafe(32),
            expires_at=timezone.now() + __import__('datetime').timedelta(hours=1)
        )
        reset_link = f"{settings.FRONTEND_URL}/auth/password/reset?token={token.token}"
        try:
            send_email(
                user=user,
                email_type=EmailLog.EmailType.PASSWORD_RESET,
                subject="Reset your password — Vermogenspeil",
                recipient=user.email,
                template_data={"reset_link": reset_link}
            )
            count += 1
        except Exception as e:
            messages.error(request, f"Failed to send to {user.email}: {str(e)}")
    messages.success(request, f"Sent {count} password reset emails")


send_password_reset_email.short_description = "Send password reset link to selected users"


def mark_email_verified(modeladmin, request, queryset):
    """Admin action: Mark selected users as email verified."""
    updated = queryset.update(email_verified=True, email_verified_at=timezone.now())
    messages.success(request, f"Marked {updated} users as verified")


mark_email_verified.short_description = "Mark selected users as email verified"


def send_test_email(modeladmin, request, queryset):
    """Admin action: Send a test email to selected users."""
    count = 0
    for user in queryset:
        try:
            send_email(
                user=user,
                email_type=EmailLog.EmailType.TEST,
                subject="Test Email — Vermogenspeil",
                recipient=user.email,
                template_data={"test_message": "This is a test email from Vermogenspeil admin panel"}
            )
            count += 1
        except Exception as e:
            messages.error(request, f"Failed to send to {user.email}: {str(e)}")
    messages.success(request, f"Sent {count} test emails")


send_test_email.short_description = "Send test email to selected users"


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("sent_at", "user", "recipient_email", "email_type", "status")
    list_filter = ("email_type", "status", "sent_at")
    search_fields = ("user__email", "recipient_email")
    readonly_fields = ("sent_at", "resend_message_id", "status_checked_at")
    ordering = ["-sent_at"]


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "subscription_tier",
        "active_tax_year",
        "email_verified",
        "is_staff",
        "is_active",
    )
    actions = [send_test_email, resend_verification_email, send_password_reset_email, mark_email_verified]
    list_filter = (
        "subscription_tier",
        "email_verified",
        "has_fiscal_partner",
        "is_staff",
        "is_active",
    )
    search_fields = ("email", "first_name", "last_name", "auth_0_id")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Persoonlijk",
            {"fields": ("first_name", "last_name", "has_fiscal_partner")},
        ),
        (
            "Abonnement & belasting",
            {
                "fields": (
                    "subscription_tier",
                    "active_tax_year",
                )
            },
        ),
        (
            "Verificatie",
            {
                "fields": (
                    "auth_0_id",
                    "email_verified",
                    "email_verified_at",
                    "terms_accepted_at",
                )
            },
        ),
        (
            "Rechten",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datums", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at", "date_joined", "last_login")


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "expires_at", "used_at")
    list_filter = ("used_at",)
    search_fields = ("user__email", "token")
    readonly_fields = ("token", "created_at", "expires_at", "used_at")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "used", "created_at")
    list_filter = ("used",)
    search_fields = ("user__email", "token")
    readonly_fields = ("token", "created_at")
