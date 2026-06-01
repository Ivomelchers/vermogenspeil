import { Navigate, Outlet, Route, useLocation } from "react-router-dom";

import AppLayout from "../components/common/AppLayout";
import AccountSettingsPage from "../pages/AccountSettingsPage";
import AddPlatformPage from "../pages/AddPlatformPage";
import DashboardPage from "../pages/DashboardPage";
import PlatformsPage from "../pages/PlatformsPage";
import AddManualAssetPage from "../pages/AddManualAssetPage";
import AddManualTransactionPage from "../pages/AddManualTransactionPage";
import PortfolioPage from "../pages/PortfolioPage";
import TransactionsPage from "../pages/TransactionsPage";
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
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/portfolio/manual/asset" element={<AddManualAssetPage />} />
        <Route path="/portfolio/manual/transaction" element={<AddManualTransactionPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/platforms" element={<PlatformsPage />} />
        <Route path="/platforms/add" element={<AddPlatformPage />} />
        <Route path="/settings/account" element={<AccountSettingsPage />} />
        <Route path="/settings/2fa" element={<TwoFactorSetupPage />} />
      </Route>
    </Route>
  );
}
