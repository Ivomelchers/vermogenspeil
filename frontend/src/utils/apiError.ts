import { isAxiosError } from "axios";

interface ApiErrorBody {
  message?: string;
  error?: string;
  data?: Record<string, unknown>;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<ApiErrorBody>(error)) {
    return error.response?.data?.message ?? fallback;
  }

  return fallback;
}

export function getApiErrorCode(error: unknown): string | undefined {
  if (isAxiosError<ApiErrorBody>(error)) {
    return error.response?.data?.error;
  }

  return undefined;
}
