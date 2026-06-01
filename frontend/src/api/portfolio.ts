import { api } from "./api";

interface ApiEnvelope<T> {
  data: T;
  error: string | null;
  message: string;
}

export interface Asset {
  id: number;
  symbol: string;
  name: string;
  asset_type: string;
  category: string;
}

export interface Position {
  id: number;
  asset: Asset;
  quantity: string;
  average_cost_eur: string | null;
  updated_at: string;
}

export interface Portfolio {
  id: number;
  name: string;
  is_default: boolean;
  positions_count: number;
  transactions_count: number;
  created_at: string;
  updated_at: string;
}

export interface PortfolioDetail extends Portfolio {
  positions: Position[];
}

export async function listPortfolios(): Promise<Portfolio[]> {
  const response = await api.get<ApiEnvelope<Portfolio[]>>("portfolios/");
  return response.data.data;
}

export async function getPortfolio(portfolioId: number): Promise<PortfolioDetail> {
  const response = await api.get<ApiEnvelope<PortfolioDetail>>(
    `portfolios/${portfolioId}/`,
  );
  return response.data.data;
}

export interface DashboardCategory {
  label: string;
  value_eur: string;
  share_percent: string;
}

export interface DashboardPosition {
  id: number;
  symbol: string;
  name: string;
  asset_type: string;
  category_label: string;
  quantity: string;
  value_eur: string;
  valuation_source?: "market" | "cost_basis";
  unit_price_eur?: string;
  price_source?: string;
}

export interface DashboardPlatform {
  id: number;
  display_name: string;
  platform: string;
  platform_display: string;
  connection_method_display: string;
  status: string;
  last_synced_at: string | null;
}

export interface DashboardYtd {
  year: number;
  available: boolean;
  start_value_eur?: string;
  current_value_eur?: string;
  ytd_return_eur?: string;
  ytd_return_percent?: string;
  start_method?: string;
  note?: string;
}

export interface DashboardReturns {
  invested_eur: string;
  unrealized_return_eur: string;
  unrealized_return_percent: string;
  method: string;
  note: string;
}

export interface DashboardSummary {
  has_portfolio: boolean;
  portfolio_id?: number;
  portfolio_name?: string;
  valuation_method: "market" | "mixed" | "cost_basis";
  valuation_note?: string;
  prices_cached?: boolean;
  as_of: string;
  total_value_eur: string;
  returns?: DashboardReturns;
  ytd?: DashboardYtd;
  positions: DashboardPosition[];
  by_category: DashboardCategory[];
  platforms: DashboardPlatform[];
  positions_count: number;
  transactions_count: number;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await api.get<ApiEnvelope<DashboardSummary>>(
    "portfolios/dashboard/",
  );
  return response.data.data;
}

export interface Transaction {
  id: number;
  asset: Asset;
  transaction_type: string;
  quantity: string;
  price_eur: string | null;
  fee_eur: string;
  total_eur: string | null;
  occurred_at: string;
  source_platform: string;
  created_at: string;
}

export async function getPortfolioTransactions(
  portfolioId: number,
): Promise<Transaction[]> {
  const response = await api.get<ApiEnvelope<Transaction[]>>(
    `portfolios/${portfolioId}/transactions/`,
  );
  return response.data.data;
}

export interface ManualAssetPayload {
  symbol: string;
  name?: string;
  asset_type: string;
  category: string;
}

export interface ManualTransactionPayload {
  asset_id: number;
  transaction_type: string;
  quantity: string;
  price_eur?: string | null;
  fee_eur?: string;
  occurred_at?: string;
  notes?: string;
}

export async function listAssets(): Promise<Asset[]> {
  const response = await api.get<ApiEnvelope<Asset[]>>("portfolios/assets/");
  return response.data.data;
}

export async function createManualAsset(payload: ManualAssetPayload): Promise<Asset> {
  const response = await api.post<ApiEnvelope<Asset>>("portfolios/assets/", payload);
  return response.data.data;
}

export async function createManualTransaction(
  portfolioId: number,
  payload: ManualTransactionPayload,
): Promise<Transaction> {
  const response = await api.post<ApiEnvelope<Transaction>>(
    `portfolios/${portfolioId}/transactions/manual/`,
    payload,
  );
  return response.data.data;
}
