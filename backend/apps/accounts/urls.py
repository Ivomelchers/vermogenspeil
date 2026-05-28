from django.urls import path

from apps.accounts.views import (
    LoginView,
    MeView,
    MfaLoginView,
    MfaStatusView,
    PasswordResetRequestView,
    PasswordResetTokenView,
    RegisterView,
    ResendVerificationView,
    ResetAuthenticatorView,
    TokenRefreshView,
    TwoFactorDisableView,
    TwoFactorSetupView,
    TwoFactorVerifyView,
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
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/login/mfa/", MfaLoginView.as_view(), name="auth-login-mfa"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/mfa/status/", MfaStatusView.as_view(), name="auth-mfa-status"),
    path("auth/2fa/setup/", TwoFactorSetupView.as_view(), name="auth-2fa-setup"),
    path("auth/2fa/verify/", TwoFactorVerifyView.as_view(), name="auth-2fa-verify"),
    path("auth/2fa/disable/", TwoFactorDisableView.as_view(), name="auth-2fa-disable"),
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
