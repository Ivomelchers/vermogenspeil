const PLATFORM_LABELS: Record<string, string> = {
  bitvavo: "Bitvavo",
  degiro: "DEGIRO",
  manual: "Handmatig",
};

export function platformLabel(platform: string): string {
  if (!platform) {
    return "—";
  }
  return PLATFORM_LABELS[platform.toLowerCase()] ?? platform;
}
