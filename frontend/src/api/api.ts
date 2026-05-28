import axios from "axios";
import { jwtDecode } from "jwt-decode";

const rawBaseURL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const baseURL = rawBaseURL.endsWith("/") ? rawBaseURL : `${rawBaseURL}/`;

interface ApiEnvelope<T> {
  data: T;
  error: string | null;
  message: string;
}

interface TokenResponse {
  access: string;
  refresh: string;
}

async function refreshAccessToken(refresh: string): Promise<TokenResponse> {
  const res = await axios.post<ApiEnvelope<TokenResponse>>(
    `${baseURL}auth/token/refresh/`,
    { refresh },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 120_000,
    },
  );
  return res.data.data;
}

export const api = axios.create({
  baseURL,
  timeout: 120_000,
  headers: {
    "Content-Type": "application/json",
  },
  paramsSerializer: (params) => {
    const parts: string[] = [];

    Object.entries(params).forEach(([key, value]) => {
      if (value === null || value === undefined) return;

      if (Array.isArray(value)) {
        const validValues = value.filter(
          (v) => v !== null && v !== undefined && v !== "",
        );
        if (validValues.length > 0) {
          const encoded = validValues
            .map((v) => encodeURIComponent(String(v)))
            .join(",");
          parts.push(`${encodeURIComponent(key)}=${encoded}`);
        }
      } else {
        parts.push(
          `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`,
        );
      }
    });

    return parts.join("&");
  },
});

api.interceptors.request.use(
  async (config) => {
    const accessToken = localStorage.getItem("access_token");
    const storedRefreshToken = localStorage.getItem("refresh_token");

    if (accessToken) {
      try {
        const decoded = jwtDecode<{ exp?: number }>(accessToken);

        if (decoded.exp && decoded.exp < Date.now() / 1000) {
          if (storedRefreshToken) {
            const tokens = await refreshAccessToken(storedRefreshToken);
            localStorage.setItem("access_token", tokens.access);
            localStorage.setItem("refresh_token", tokens.refresh);
            config.headers.Authorization = `Bearer ${tokens.access}`;
          } else {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
          }
        } else {
          config.headers.Authorization = `Bearer ${accessToken}`;
        }
      } catch {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
    }

    if (config.method?.toLowerCase() === "get") {
      config.params = {
        ...config.params,
        _t: Date.now(),
      };
    }

    return config;
  },
  (error) => Promise.reject(error),
);
