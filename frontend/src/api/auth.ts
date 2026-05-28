import axios, { isAxiosError } from "axios";

import { api, authApi } from "./api";

const rawBaseURL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const baseURL = rawBaseURL.endsWith("/") ? rawBaseURL : `${rawBaseURL}/`;

interface ApiEnvelope<T> {
  data: T;
  error: string | null;
  message: string;
}

export interface AuthUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email_verified: boolean;
  subscription_tier: "free" | "premium";
  is_premium: boolean;
  active_tax_year: number;
  has_fiscal_partner: boolean;
}

export interface Auth0TokenResponse {
  id_token: string;
  access_token: string;
  refresh_token: string;
}

export interface Auth0Authenticator {
  id: string;
  authenticator_type: "otp" | "oob";
  active: boolean;
}

export const auth = async (): Promise<AuthUser> => {
  const res = await api.get<ApiEnvelope<AuthUser>>("auth/me/");
  return res.data.data;
};

export const login = async ({
  email,
  password,
}: {
  email: string;
  password: string;
}): Promise<Auth0TokenResponse> => {
  const res = await api.post<ApiEnvelope<Auth0TokenResponse>>("auth/login/", {
    email,
    password,
  });
  return res.data.data;
};

export const refreshToken = async (refreshTokenValue: string): Promise<Auth0TokenResponse> => {
  const res = await axios.post<ApiEnvelope<Auth0TokenResponse>>(
    `${baseURL}auth/token/refresh/`,
    { refresh: refreshTokenValue },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 120_000,
    },
  );
  return res.data.data;
};

export const getAuthenticators = async (mfaToken: string): Promise<Auth0Authenticator[]> => {
  const res = await authApi.get<Auth0Authenticator[]>("mfa/authenticators", {
    headers: {
      Authorization: `Bearer ${mfaToken}`,
    },
  });
  return res.data.filter(
    (authenticator) => authenticator.active && authenticator.authenticator_type === "otp",
  );
};

export const confirmOtpChallenge = async (data: {
  mfa_token: string;
  otp: string;
}): Promise<Auth0TokenResponse> => {
  const res = await authApi.post<Auth0TokenResponse>("/oauth/token", {
    client_id: import.meta.env.VITE_AUTH0_CLIENT_ID,
    audience: `https://${import.meta.env.VITE_AUTH0_DOMAIN}/api/v2/`,
    grant_type: "http://auth0.com/oauth/grant-type/mfa-otp",
    scope: "openid profile email offline_access",
    mfa_token: data.mfa_token,
    otp: data.otp,
  });
  return res.data;
};

export const enrollAuthenticator = async (mfaToken: string) => {
  const res = await authApi.post(
    "mfa/associate/",
    { authenticator_types: ["otp"] },
    { headers: { Authorization: `Bearer ${mfaToken}` } },
  );
  return res.data as { secret: string; barcode_uri: string };
};

export const enrollAuthenticatorConfirm = async (data: {
  mfa_token: string;
  otp: string;
  client_secret: string;
}): Promise<Auth0TokenResponse> => {
  const res = await authApi.post<Auth0TokenResponse>("/oauth/token", {
    client_id: import.meta.env.VITE_AUTH0_CLIENT_ID,
    audience: `https://${import.meta.env.VITE_AUTH0_DOMAIN}/api/v2/`,
    grant_type: "http://auth0.com/oauth/grant-type/mfa-otp",
    scope: "openid profile email offline_access",
    mfa_token: data.mfa_token,
    client_secret: data.client_secret,
    otp: data.otp,
  });
  return res.data;
};

export const register = async (data: {
  email: string;
  password: string;
  first_name: string;
  terms_accepted: boolean;
}) => {
  const res = await api.post<ApiEnvelope<unknown>>("auth/register/", data);
  return res.data;
};

export const verifyEmail = async (token: string) => {
  const res = await api.post<ApiEnvelope<{ email: string; email_verified: boolean }>>(
    "auth/verify-email/",
    { token },
  );
  return res.data;
};

export const resendVerificationEmail = async (email: string) => {
  const res = await api.post<ApiEnvelope<null>>("auth/resend-verification/", { email });
  return res.data;
};

export const requestPasswordReset = async (email: string) => {
  const res = await api.post<ApiEnvelope<null>>("auth/password/reset/", { email });
  return res.data;
};

export const validatePasswordResetToken = async (token: string) => {
  const res = await axios.get<ApiEnvelope<{ email: string }>>(
    `${baseURL}auth/password/reset/${token}/`,
    { timeout: 120_000 },
  );
  return res.data;
};

export const confirmPasswordReset = async (token: string, password: string) => {
  const res = await axios.post<ApiEnvelope<{ email: string }>>(
    `${baseURL}auth/password/reset/${token}/`,
    { password },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 120_000,
    },
  );
  return res.data;
};

export const resetMfa = async () => {
  const res = await api.post<ApiEnvelope<null>>("auth/mfa/reset/");
  return res.data;
};

export function isAuth0MfaRequired(error: unknown): boolean {
  if (isAxiosError<ApiEnvelope<{ mfa_token?: string }>>(error)) {
    const body = error.response?.data;
    return body?.error === "mfa_required" && Boolean(body?.data?.mfa_token);
  }
  return false;
}

export function getAuth0MfaToken(error: unknown): string | undefined {
  if (isAxiosError<ApiEnvelope<{ mfa_token?: string }>>(error)) {
    return error.response?.data?.data?.mfa_token;
  }
  return undefined;
}

export function isAuth0EnrollmentRequired(error: unknown): boolean {
  if (isAxiosError<ApiEnvelope<{ mfa_token?: string }>>(error)) {
    return error.response?.data?.error === "enrollment_required";
  }
  return false;
}

export function getAuth0EnrollmentMfaToken(error: unknown): string | undefined {
  if (isAxiosError<ApiEnvelope<{ mfa_token?: string }>>(error)) {
    return error.response?.data?.data?.mfa_token;
  }
  return undefined;
}
