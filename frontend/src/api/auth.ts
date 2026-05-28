import axios, { isAxiosError } from "axios";

import { api } from "./api";

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
  is_2fa_enabled: boolean;
}

export interface Auth0TokenResponse {
  id_token: string;
  access_token: string;
  refresh_token: string;
}

export interface MfaStatus {
  enrolled: boolean;
  status_available?: boolean;
}

export interface TwoFactorSetupResponse {
  secret: string;
  barcode_uri: string;
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

export const completeMfaLogin = async (data: {
  mfa_token: string;
  otp?: string;
  backup_code?: string;
}): Promise<Auth0TokenResponse> => {
  const res = await axios.post<ApiEnvelope<Auth0TokenResponse>>(
    `${baseURL}auth/login/mfa/`,
    data,
    {
      headers: { "Content-Type": "application/json" },
      timeout: 120_000,
    },
  );
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

export const getMfaStatus = async (): Promise<MfaStatus> => {
  const res = await api.get<ApiEnvelope<MfaStatus>>("auth/mfa/status/");
  return res.data.data;
};

export const startTwoFactorSetup = async (): Promise<TwoFactorSetupResponse> => {
  const res = await api.post<ApiEnvelope<TwoFactorSetupResponse>>("auth/2fa/setup/");
  return res.data.data;
};

export const verifyTwoFactorSetup = async (
  otp: string,
): Promise<{ backup_codes: string[] }> => {
  const res = await api.post<ApiEnvelope<{ backup_codes: string[] }>>("auth/2fa/verify/", {
    otp,
  });
  return res.data.data;
};

export const disableTwoFactor = async (password: string, otp: string) => {
  const res = await api.post<ApiEnvelope<null>>("auth/2fa/disable/", { password, otp });
  return res.data;
};

const LOCAL_MFA_TOKEN_MAX_LENGTH = 64;

export function isMfaRequired(error: unknown): boolean {
  if (isAxiosError<ApiEnvelope<{ mfa_token?: string }>>(error)) {
    const body = error.response?.data;
    const token = body?.data?.mfa_token ?? "";
    return (
      body?.error === "mfa_required" &&
      token.length > 0 &&
      token.length <= LOCAL_MFA_TOKEN_MAX_LENGTH
    );
  }
  return false;
}

export function getMfaToken(error: unknown): string | undefined {
  if (isAxiosError<ApiEnvelope<{ mfa_token?: string }>>(error)) {
    return error.response?.data?.data?.mfa_token;
  }
  return undefined;
}
