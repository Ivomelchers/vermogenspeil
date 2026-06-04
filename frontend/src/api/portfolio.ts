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

export async function getPortfolio(
  portfolioId: number,
): Promise<PortfolioDetail> {
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
  asset_id?: number;
  category?: string;
  symbol: string;
  name: string;
  asset_type: string;
  category_label: string;
  quantity: string;
  value_eur: string;
  cost_basis_eur?: string;
  average_cost_eur?: string;
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
  trusted?: boolean;
  start_value_eur?: string;
  current_value_eur?: string;
  ytd_return_eur?: string;
  ytd_return_percent?: string;
  start_method?: string;
  current_method?: string;
  note?: string;
}

export interface DashboardMetricsTrust {
  invested_trusted: boolean;
  ytd_trusted: boolean;
  has_warnings: boolean;
  warnings: string[];
  missing_price_symbols: string[];
}

export interface DashboardReturns {
  invested_eur: string;
  cost_basis_eur?: string;
  total_buy_outflow_eur?: string;
  unrealized_return_eur: string;
  unrealized_return_percent: string;
  method: string;
  note: string;
}

export interface DashboardValuePoint {
  date: string;
  value_eur: string;
  cost_basis_eur?: string;
  method: "cost_basis" | "current" | "ytd_start" | "historical";
}

export interface DashboardMover {
  position_id: number;
  symbol: string;
  name: string;
  start_value_eur: string;
  current_value_eur: string;
  change_eur: string;
  change_percent: string;
}

export interface DashboardMoversPeriod {
  period: string;
  period_start: string;
  gainers: DashboardMover[];
  losers: DashboardMover[];
}

export type DashboardMoversByPeriod = Partial<
  Record<"day" | "week" | "month" | "ytd", DashboardMoversPeriod>
>;

export interface DashboardHeroDelta {
  available: boolean;
  start_date?: string;
  start_value_eur?: string;
  change_eur?: string;
  change_percent?: string;
  note?: string;
}

export interface DashboardActivity {
  id: number;
  occurred_at: string;
  symbol: string;
  transaction_type: string;
  transaction_type_label: string;
  source_platform: string;
  quantity: string;
  total_eur: string | null;
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
  metrics_trust?: DashboardMetricsTrust;
  positions: DashboardPosition[];
  by_category: DashboardCategory[];
  platforms: DashboardPlatform[];
  positions_count: number;
  transactions_count: number;
  recent_activity: DashboardActivity[];
  value_history: DashboardValuePoint[];
  hero_delta_30d?: DashboardHeroDelta;
  movers?: DashboardMoversByPeriod;
}

export async function updateAssetCategory(
  assetId: number,
  category: string,
): Promise<Asset> {
  const response = await api.patch<ApiEnvelope<Asset>>(
    `portfolios/assets/${assetId}/category/`,
    { category },
  );
  return response.data.data;
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

export interface TransactionListFilters {
  platforms: string[];
  transaction_types: string[];
  symbols: string[];
}

export interface TransactionListParams {
  page?: number;
  page_size?: number;
  sort?: string;
  order?: "asc" | "desc";
  platform?: string;
  transaction_type?: string;
  symbol?: string;
  date_from?: string;
  date_to?: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  filters: TransactionListFilters;
}

export async function getPortfolioTransactions(
  portfolioId: number,
  params: TransactionListParams = {},
): Promise<TransactionListResponse> {
  const response = await api.get<ApiEnvelope<TransactionListResponse>>(
    `portfolios/${portfolioId}/transactions/`,
    { params },
  );
  return response.data.data;
}

/** Download CSV met huidige filterset (FSD §7). */
export async function downloadPortfolioTransactionsCsv(
  portfolioId: number,
  params: TransactionListParams = {},
): Promise<void> {
  const response = await api.get(
    `portfolios/${portfolioId}/transactions/export/`,
    {
      params,
      responseType: "blob",
    },
  );
  const blob = new Blob([response.data], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `transacties-${portfolioId}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
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

export async function createManualAsset(
  payload: ManualAssetPayload,
): Promise<Asset> {
  const response = await api.post<ApiEnvelope<Asset>>(
    "portfolios/assets/",
    payload,
  );
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
