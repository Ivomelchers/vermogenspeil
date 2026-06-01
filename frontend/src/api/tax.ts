import { api } from "./api";

interface ApiEnvelope<T> {
  data: T;
  error: string | null;
  message: string;
}

export interface TaxYearContext {
  relevant_tax_year: number;
  peildatum: string;
  timezone: string;
  switched_on_may_first: boolean;
  rule: string;
  user_active_tax_year?: number;
}

export interface ForfaitairCalculation {
  inputs: Record<string, string>;
  steps: Record<string, string>;
  tax_due_eur: string;
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
  calculation?: ForfaitairCalculation;
}

export interface WerkelijkBox3Summary {
  available: boolean;
  year: number;
  method?: string;
  message?: string;
  tax_due_eur?: string;
  is_provisional?: boolean;
  provisional_note?: string;
  disclaimer?: string;
  calculation?: {
    tax_due_eur: string;
    werkelijk_rendement_eur: string;
    werkelijk_percent: string;
    components: Record<string, string>;
    w_start_eur: string;
    w_end_eur: string;
    netto_inleg_eur: string;
  };
}

export interface Box3Comparison {
  forfait_tax_eur: string;
  werkelijk_tax_eur: string;
  applied_tax_eur: string;
  savings_eur: string;
  werkelijk_is_beneficial: boolean;
  recommended_method: string;
  message: string;
}

export interface Box3Summary {
  year: number;
  is_premium: boolean;
  forfaitair: ForfaitairBox3Summary;
  werkelijk: WerkelijkBox3Summary;
  comparison: Box3Comparison | null;
  applied_tax_eur: string | null;
  tax_warnings?: string[];
  message: string;
}

export interface Box3Report {
  year: number;
  generated_at: string;
  forfaitair: ForfaitairBox3Summary;
  werkelijk: WerkelijkBox3Summary;
  comparison?: Box3Comparison;
  positions_start: Array<Record<string, string | undefined>>;
  positions_end: Array<Record<string, string | undefined>>;
  income_and_cashflows: Array<Record<string, string | null | undefined>>;
  excluded_from_werkelijk: string[];
  not_included_yet: string[];
  manual_assets?: Record<string, unknown>;
}

export interface Box3BankBalance {
  id: number;
  tax_year: number;
  label: string;
  account_type: string;
  balance_eur: string;
  institution: string;
  notes: string;
}

export interface Box3Debt {
  id: number;
  tax_year: number;
  label: string;
  debt_type: string;
  outstanding_eur: string;
  interest_paid_ytd_eur: string;
  creditor: string;
  linked_real_estate: number | null;
  notes: string;
}

export interface Box3RealEstate {
  id: number;
  tax_year: number;
  label: string;
  property_type: string;
  value_eur: string;
  is_abroad: boolean;
  annual_rent_eur: string;
  vacancy_ratio: string;
  rental_income_ytd_eur: string;
  eigen_gebruik_days: number;
  eigen_gebruik_days_computed?: number;
  verhuur_days: number;
  verbouw_days: number;
  bijtelling_method: string;
  economic_rent_yearly_eur: string;
  woz_previous_year_eur: string;
  bijtelling_rate: string;
  bijtelling_eur?: string;
  notes: string;
}

export type Box3BankBalanceInput = Omit<Box3BankBalance, "id">;
export type Box3DebtInput = Omit<Box3Debt, "id">;
export type Box3RealEstateInput = Omit<Box3RealEstate, "id">;

export async function getTaxYearContext(): Promise<TaxYearContext> {
  const response = await api.get<ApiEnvelope<TaxYearContext>>("tax/context/");
  return response.data.data;
}

export async function getForfaitairBox3(year: number): Promise<ForfaitairBox3Summary> {
  const response = await api.get<ApiEnvelope<ForfaitairBox3Summary>>(
    `tax/box3/forfaitair/${year}/`,
  );
  return response.data.data;
}

export async function getBox3Summary(year: number): Promise<Box3Summary> {
  const response = await api.get<ApiEnvelope<Box3Summary>>(`tax/box3/${year}/`);
  return response.data.data;
}

export async function downloadBox3ReportPdf(year: number): Promise<Blob> {
  // Geen Accept: application/pdf — DRF heeft alleen JSON-renderers en geeft dan 406.
  const response = await api.get(`tax/box3/${year}/report/`, {
    params: { export: "pdf" },
    responseType: "blob",
  });
  const blob = response.data as Blob;
  const contentType = String(response.headers["content-type"] ?? "");

  if (!contentType.includes("application/pdf")) {
    const text = await blob.text();
    let message = "PDF laden mislukt. Herstart de backend (runserver) na een update.";
    try {
      const parsed = JSON.parse(text) as { message?: string; detail?: string };
      message = parsed.message ?? parsed.detail ?? message;
    } catch {
      // non-JSON body (bijv. lege 404)
    }
    throw new Error(message);
  }

  return blob;
}

export async function listBox3BankBalances(year: number): Promise<Box3BankBalance[]> {
  const response = await api.get<ApiEnvelope<Box3BankBalance[]>>("tax/manual/bank-balances/", {
    params: { year },
  });
  return response.data.data;
}

export async function createBox3BankBalance(
  payload: Box3BankBalanceInput,
): Promise<Box3BankBalance> {
  const response = await api.post<ApiEnvelope<Box3BankBalance>>(
    "tax/manual/bank-balances/",
    payload,
  );
  return response.data.data;
}

export async function deleteBox3BankBalance(id: number): Promise<void> {
  await api.delete(`tax/manual/bank-balances/${id}/`);
}

export async function listBox3Debts(year: number): Promise<Box3Debt[]> {
  const response = await api.get<ApiEnvelope<Box3Debt[]>>("tax/manual/debts/", {
    params: { year },
  });
  return response.data.data;
}

export async function createBox3Debt(payload: Box3DebtInput): Promise<Box3Debt> {
  const response = await api.post<ApiEnvelope<Box3Debt>>("tax/manual/debts/", payload);
  return response.data.data;
}

export async function updateBox3Debt(
  id: number,
  payload: Partial<Box3DebtInput>,
): Promise<Box3Debt> {
  const response = await api.patch<ApiEnvelope<Box3Debt>>(`tax/manual/debts/${id}/`, payload);
  return response.data.data;
}

export async function deleteBox3Debt(id: number): Promise<void> {
  await api.delete(`tax/manual/debts/${id}/`);
}

export async function listBox3RealEstate(year: number): Promise<Box3RealEstate[]> {
  const response = await api.get<ApiEnvelope<Box3RealEstate[]>>("tax/manual/real-estate/", {
    params: { year },
  });
  return response.data.data;
}

export async function createBox3RealEstate(payload: Box3RealEstateInput): Promise<Box3RealEstate> {
  const response = await api.post<ApiEnvelope<Box3RealEstate>>(
    "tax/manual/real-estate/",
    payload,
  );
  return response.data.data;
}

export async function updateBox3RealEstate(
  id: number,
  payload: Partial<Box3RealEstateInput>,
): Promise<Box3RealEstate> {
  const response = await api.patch<ApiEnvelope<Box3RealEstate>>(
    `tax/manual/real-estate/${id}/`,
    payload,
  );
  return response.data.data;
}

export async function deleteBox3RealEstate(id: number): Promise<void> {
  await api.delete(`tax/manual/real-estate/${id}/`);
}
