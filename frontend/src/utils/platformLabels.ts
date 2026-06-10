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

/** Platformen met live API-koppeling (crypto + brokers). */
export const LIVE_API_PLATFORMS = [
  { id: "bitvavo", name: "Bitvavo", needsSecret: true, needsPassphrase: false },
  { id: "bybit", name: "Bybit", needsSecret: true, needsPassphrase: false },
  { id: "okx", name: "OKX", needsSecret: true, needsPassphrase: true },
  { id: "trading212", name: "Trading 212", needsSecret: false, needsPassphrase: false },
  { id: "trade_republic", name: "Trade Republic", needsSecret: false, needsPassphrase: false },
] as const;

/** @deprecated Gebruik LIVE_API_PLATFORMS */
export const LIVE_API_CRYPTO_PLATFORMS = LIVE_API_PLATFORMS.filter(
  (p) => p.id === "bitvavo" || p.id === "bybit" || p.id === "okx",
);
