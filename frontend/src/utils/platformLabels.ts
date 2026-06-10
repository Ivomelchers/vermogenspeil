const PLATFORM_LABELS: Record<string, string> = {
  bitvavo: "Bitvavo",
  bybit: "Bybit",
  okx: "OKX",
  degiro: "DEGIRO",
  trading212: "Trading 212",
  trade_republic: "Trade Republic",
  manual: "Handmatig",
};

export function platformLabel(platform: string): string {
  if (!platform) {
    return "—";
  }
  return PLATFORM_LABELS[platform.toLowerCase()] ?? platform;
}

/** CSV-platformen met live import in de app. */
export const LIVE_CSV_PLATFORMS = [
  { id: "degiro", name: "DEGIRO" },
  { id: "trading212", name: "Trading 212" },
  { id: "trade_republic", name: "Trade Republic" },
  { id: "bybit", name: "Bybit" },
  { id: "okx", name: "OKX" },
] as const;

/** Crypto-platformen met live API-koppeling. */
export const LIVE_API_CRYPTO_PLATFORMS = [
  { id: "bitvavo", name: "Bitvavo", needsPassphrase: false },
  { id: "bybit", name: "Bybit", needsPassphrase: false },
  { id: "okx", name: "OKX", needsPassphrase: true },
] as const;
