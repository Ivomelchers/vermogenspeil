import { api } from "./api";

interface ApiEnvelope<T> {
  data: T;
  error: string | null;
  message: string;
}

export interface ForfaitairBox3Summary {
  available: boolean;
  year: number;
  method?: string;
  message?: string;
  tax_due_eur?: string;
  snapshot_total_eur?: string;
  parameters_provisional?: boolean;
  disclaimer?: string;
  box3_inputs?: {
    banktegoeden_eur: string;
    overige_bezittingen_eur: string;
    schulden_eur: string;
  };
  calculation?: {
    tax_due_eur: string;
    steps: Record<string, string>;
  };
}

export async function getForfaitairBox3(year: number): Promise<ForfaitairBox3Summary> {
  const response = await api.get<ApiEnvelope<ForfaitairBox3Summary>>(
    `tax/box3/forfaitair/${year}/`,
  );
  return response.data.data;
}
