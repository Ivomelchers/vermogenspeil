export const TX_TYPE_LABELS: Record<string, string> = {
  buy: "Aankoop",
  sell: "Verkoop",
  dividend: "Dividend",
  deposit: "Storting",
  withdrawal: "Opname",
  fee: "Kosten",
  other: "Overig",
};

export const TX_TYPE_COLORS: Record<string, string> = {
  buy: "moss",
  sell: "ochre",
  dividend: "azure",
  deposit: "moss",
  withdrawal: "taupe",
  fee: "red",
  other: "gray",
};

export function transactionTypeLabel(type: string): string {
  return TX_TYPE_LABELS[type] ?? type;
}

export function transactionTypeColor(type: string): string {
  return TX_TYPE_COLORS[type] ?? "gray";
}

export const ASSET_TYPE_LABELS: Record<string, string> = {
  stock: "Aandeel",
  etf: "ETF",
  crypto: "Crypto",
  cash: "Cash",
  bond: "Obligatie",
  other: "Overig",
};

export const FISCAL_CATEGORY_LABELS: Record<string, string> = {
  belegging: "Belegging",
  banktegoed: "Banktegoed",
  edelmetaal: "Edelmetaal",
  schuld: "Schuld",
  overig: "Overig",
};
