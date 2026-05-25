from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import EmailVerificationToken, User


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
    list_filter = (
        "subscription_tier",
        "email_verified",
        "has_fiscal_partner",
        "is_staff",
        "is_active",
    )
    search_fields = ("email", "first_name", "last_name")

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
