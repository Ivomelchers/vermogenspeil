import { api } from "./api";

export interface HealthResponse {
  data: { status: string };
  error: string | null;
  message: string;
}

export const checkHealth = async (): Promise<HealthResponse> => {
  const res = await api.get("health/");
  return res.data;
};
