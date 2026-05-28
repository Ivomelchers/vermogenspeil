from django.urls import path

from apps.accounts.views import (
    MeView,
    PasswordResetRequestView,
    PasswordResetTokenView,
    RegisterView,
    ResendVerificationView,
    ResetAuthenticatorView,
    VerifyEmailView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path(
        "auth/resend-verification/",
        ResendVerificationView.as_view(),
        name="auth-resend-verification",
    ),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/mfa/reset/", ResetAuthenticatorView.as_view(), name="auth-mfa-reset"),
    path(
        "auth/password/reset/",
        PasswordResetRequestView.as_view(),
        name="auth-password-reset-request",
    ),
    path(
        "auth/password/reset/<str:token>/",
        PasswordResetTokenView.as_view(),
        name="auth-password-reset-token",
    ),
]
