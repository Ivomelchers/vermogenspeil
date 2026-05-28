import { Navigate, Outlet, Route, useLocation } from "react-router-dom";

import AppLayout from "../components/common/AppLayout";
import AccountSettingsPage from "../pages/AccountSettingsPage";
import DashboardPage from "../pages/DashboardPage";
import TwoFactorSetupPage from "../pages/TwoFactorSetupPage";
import { useUser } from "../contexts/UserContext";

function PrivateAuthGuard() {
  const { isAuthenticated } = useUser();
  const location = useLocation();

  if (!isAuthenticated) {
    return (
      <Navigate to="/auth/login" replace state={{ from: location.pathname }} />
    );
  }

  return <Outlet />;
}

export function PrivateRoutes() {
  return (
    <Route element={<PrivateAuthGuard />}>
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/settings/account" element={<AccountSettingsPage />} />
        <Route path="/settings/2fa" element={<TwoFactorSetupPage />} />
      </Route>
    </Route>
  );
}
