import { api } from "./api";

interface ApiEnvelope<T> {
  data: T;
  error: string | null;
  message: string;
}

export interface LivePriceQuote {
  symbol: string;
  asset_type: string;
  price_eur: string;
  source: string;
  fetched_at: string;
  from_cache: boolean;
}

export async function getLiveQuotes(
  symbols: string[],
  assetType: string,
): Promise<LivePriceQuote[]> {
  const params = new URLSearchParams({
    symbols: symbols.join(","),
    asset_type: assetType,
  });
  const response = await api.get<ApiEnvelope<{ quotes: LivePriceQuote[] }>>(
    `pricing/quotes/?${params.toString()}`,
  );
  return response.data.data.quotes;
}
