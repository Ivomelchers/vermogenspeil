import { Navigate, Outlet, Route, useLocation } from "react-router-dom";

import PublicLayout from "../components/common/PublicLayout";
import HomePage from "../pages/HomePage";
import LoginPage from "../pages/LoginPage";
import OtpChallengePage from "../pages/OtpChallengePage";
import PasswordResetConfirmPage from "../pages/PasswordResetConfirmPage";
import PasswordResetRequestPage from "../pages/PasswordResetRequestPage";
import RegisterPage from "../pages/RegisterPage";
import ResendVerificationPage from "../pages/ResendVerificationPage";
import VerifyEmailPage from "../pages/VerifyEmailPage";
import { useUser } from "../contexts/UserContext";

const PUBLIC_AUTH_EXCEPTIONS = new Set([
  "/auth/change-password",
  "/auth/password/forgot",
  "/auth/password/reset",
  "/auth/otp-challenge",
]);

function PublicAuthGuard() {
  const { isAuthenticated } = useUser();
  const location = useLocation();

  if (isAuthenticated && !PUBLIC_AUTH_EXCEPTIONS.has(location.pathname)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

export function PublicRoutes() {
  return (
    <>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
      </Route>

      <Route path="/auth/verify-email" element={<VerifyEmailPage />} />
      <Route path="/auth/resend-verification" element={<ResendVerificationPage />} />
      <Route path="/auth/password/forgot" element={<PasswordResetRequestPage />} />
      <Route path="/auth/password/reset" element={<PasswordResetConfirmPage />} />

      <Route element={<PublicAuthGuard />}>
        <Route path="/auth/login" element={<LoginPage />} />
        <Route path="/auth/register" element={<RegisterPage />} />
        <Route path="/auth/otp-challenge" element={<OtpChallengePage />} />
      </Route>
    </>
  );
}
