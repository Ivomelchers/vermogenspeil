import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * Bridge page that receives the OAuth callback from the backend
 * and redirects to the appropriate success/error page in the hash router.
 * This is necessary because the backend redirects to a non-hash URL,
 * but the frontend uses hash-based routing.
 */
export function SaxoCallbackSuccessBridge() {
  const [searchParams] = useSearchParams();
  const connectionId = searchParams.get("connection_id");

  useEffect(() => {
    if (connectionId) {
      window.location.href = `/#/auth/saxo/success?connection_id=${connectionId}`;
    } else {
      window.location.href = "/#/auth/saxo/error?error=missing_param&description=Missing connection_id";
    }
  }, [connectionId]);

  return <div style={{ padding: "2rem", textAlign: "center" }}>Procesamos tu conexión...</div>;
}

export function SaxoCallbackErrorBridge() {
  const [searchParams] = useSearchParams();
  const error = searchParams.get("error");
  const description = searchParams.get("description");

  useEffect(() => {
    const params = new URLSearchParams();
    if (error) params.set("error", error);
    if (description) params.set("description", description);
    window.location.href = `/#/auth/saxo/error?${params.toString()}`;
  }, [error, description]);

  return <div style={{ padding: "2rem", textAlign: "center" }}>Redireccionando a la página de error...</div>;
}
