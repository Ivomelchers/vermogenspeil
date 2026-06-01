import { isAxiosError } from "axios";

import { api } from "./api";

interface ApiEnvelope<T> {
  data: T;
  error: string | null;
  message: string;
}

export interface PeildatumSnapshot {
  id: number;
  year: number;
  peildatum: string;
  total_value_eur: string;
  valuation_method: "market" | "mixed" | "cost_basis";
  data: {
    year: number;
    peildatum: string;
    captured_at: string;
    timezone: string;
    has_portfolio: boolean;
    valuation_method: string;
    total_value_eur: string;
    positions: Array<{
      symbol: string;
      name: string;
      value_eur: string;
      valuation_source?: string;
      unit_price_eur?: string;
    }>;
    by_category: Array<{
      label: string;
      value_eur: string;
      share_percent: string;
    }>;
    note?: string;
  };
  created_at: string;
}

export async function listPeildatumSnapshots(): Promise<PeildatumSnapshot[]> {
  const response = await api.get<ApiEnvelope<PeildatumSnapshot[]>>(
    "snapshots/peildatum/",
  );
  return response.data.data;
}

export async function getPeildatumSnapshot(
  year: number,
): Promise<PeildatumSnapshot | null> {
  try {
    const response = await api.get<ApiEnvelope<PeildatumSnapshot>>(
      `snapshots/peildatum/${year}/`,
    );
    return response.data.data;
  } catch (error) {
    if (isAxiosError(error) && error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function createPeildatumSnapshot(year: number): Promise<PeildatumSnapshot> {
  const response = await api.post<ApiEnvelope<PeildatumSnapshot>>(
    "snapshots/peildatum/create/",
    { year },
  );
  return response.data.data;
}
