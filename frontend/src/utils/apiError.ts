import { isAxiosError } from "axios";

interface ApiErrorBody {
  message?: string;
  error?: string;
  data?: Record<string, unknown>;
}

async function messageFromBlob(blob: Blob): Promise<string | null> {
  try {
    const text = await blob.text();
    const parsed = JSON.parse(text) as ApiErrorBody & { detail?: string };
    return parsed.message ?? parsed.detail ?? null;
  } catch {
    return null;
  }
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError<ApiErrorBody | Blob>(error)) {
    const data = error.response?.data;
    if (data && typeof data === "object" && "message" in data && data.message) {
      return data.message;
    }
    if (data instanceof Blob) {
      // Sync fallback; callers that need detail should use getApiErrorMessageAsync.
      return fallback;
    }
    const detail = (data as { detail?: string } | undefined)?.detail;
    if (detail) {
      return detail;
    }
  }

  return fallback;
}

export async function getApiErrorMessageAsync(
  error: unknown,
  fallback: string,
): Promise<string> {
  if (isAxiosError<ApiErrorBody | Blob>(error)) {
    const data = error.response?.data;
    if (data instanceof Blob) {
      const fromBlob = await messageFromBlob(data);
      if (fromBlob) {
        return fromBlob;
      }
    }
    return getApiErrorMessage(error, fallback);
  }

  return fallback;
}

export function getApiErrorCode(error: unknown): string | undefined {
  if (isAxiosError<ApiErrorBody>(error)) {
    return error.response?.data?.error;
  }

  return undefined;
}
