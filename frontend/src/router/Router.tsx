import { Navigate, Route, Routes } from "react-router-dom";

import AuthLoading from "../components/common/AuthLoading";
import { useUser } from "../contexts/UserContext";
import { PrivateRoutes } from "./PrivateRoutes";
import { PublicRoutes } from "./PublicRoutes";

export default function Router() {
  const { loading } = useUser();

  if (loading) {
    return <AuthLoading />;
  }

  return (
    <Routes>
      {PublicRoutes()}
      {PrivateRoutes()}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
