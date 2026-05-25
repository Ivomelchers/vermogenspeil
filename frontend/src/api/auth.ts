import { api } from "./api";

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface TokenResponse {
  access: string;
  refresh: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export const login = async (
  credentials: LoginCredentials,
): Promise<TokenResponse> => {
  const res = await api.post("auth/login/", credentials);
  return res.data;
};

export const refreshToken = async (refresh: string): Promise<TokenResponse> => {
  const res = await api.post("auth/token/refresh/", { refresh });
  return res.data;
};

export const logout = async () => {
  const res = await api.post("auth/logout/");
  return res.data;
};

export const register = async (data: RegisterPayload) => {
  const res = await api.post("auth/register/", data);
  return res.data;
};

export const verifyEmail = async (token: string) => {
  const res = await api.post("auth/verify-email/", { token });
  return res.data;
};

export const sendPasswordResetEmail = async (email: string) => {
  const res = await api.post("auth/password/reset/", { email });
  return res.data;
};

export const checkPasswordResetToken = async (token: string) => {
  const res = await api.get(`auth/password/reset/${token}/`);
  return res.data;
};

export const resetPassword = async (data: {
  token: string;
  password: string;
}) => {
  const res = await api.post(`auth/password/reset/${data.token}/`, {
    password: data.password,
  });
  return res.data;
};

export const setupTwoFactor = async () => {
  const res = await api.post("auth/2fa/setup/");
  return res.data;
};

export const verifyTwoFactor = async (otp: string) => {
  const res = await api.post("auth/2fa/verify/", { otp });
  return res.data;
};

export const disableTwoFactor = async () => {
  const res = await api.post("auth/2fa/disable/");
  return res.data;
};
