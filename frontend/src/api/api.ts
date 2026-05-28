import axios from "axios";
import { jwtDecode } from "jwt-decode";

import { refreshToken } from "./auth";

const rawBaseURL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const baseURL = rawBaseURL.endsWith("/") ? rawBaseURL : `${rawBaseURL}/`;

type LogoutListener = () => void;
const logoutListeners = new Set<LogoutListener>();

export const eventEmitter = {
  on(_event: "logout", listener: LogoutListener) {
    logoutListeners.add(listener);
    return () => {
      logoutListeners.delete(listener);
    };
  },
  emit(_event: "logout") {
    logoutListeners.forEach((listener) => listener());
  },
};

let refreshInFlight: ReturnType<typeof refreshToken> | null = null;

export const api = axios.create({
  baseURL,
  timeout: 120_000,
  headers: {
    "Content-Type": "application/json",
  },
});

export const authApi = axios.create({
  baseURL: `https://${import.meta.env.VITE_AUTH0_DOMAIN}`,
  timeout: 10_000,
});

api.interceptors.request.use(async (config) => {
  const idToken = localStorage.getItem("id_token");
  const storedRefreshToken = localStorage.getItem("refresh_token");

  if (idToken) {
    try {
      const decoded = jwtDecode<{ exp?: number }>(idToken);

      if (decoded.exp && decoded.exp < Date.now() / 1000) {
        if (
          localStorage.getItem("rememberMe") === "true" &&
          storedRefreshToken
        ) {
          if (!refreshInFlight) {
            refreshInFlight = refreshToken(storedRefreshToken).finally(() => {
              refreshInFlight = null;
            });
          }

          const tokens = await refreshInFlight;
          localStorage.setItem("id_token", tokens.id_token);
          localStorage.setItem("access_token", tokens.access_token);
          localStorage.setItem("refresh_token", tokens.refresh_token);
          config.headers.Authorization = `Bearer ${tokens.id_token}`;
        } else {
          eventEmitter.emit("logout");
        }
      } else {
        config.headers.Authorization = `Bearer ${idToken}`;
      }
    } catch {
      config.headers.Authorization = `Bearer ${idToken}`;
    }
  }

  if (config.method?.toLowerCase() === "get") {
    config.params = {
      ...config.params,
      _t: Date.now(),
    };
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url ?? "";
    const isPublicAuthRequest =
      requestUrl.includes("auth/login/") ||
      requestUrl.includes("auth/register/") ||
      requestUrl.includes("auth/verify-email/") ||
      requestUrl.includes("auth/resend-verification/") ||
      requestUrl.includes("auth/password/reset/") ||
      requestUrl.includes("auth/token/refresh/");

    if (error.response?.status === 401 && !isPublicAuthRequest) {
      eventEmitter.emit("logout");
    }

    return Promise.reject(error);
  },
);
