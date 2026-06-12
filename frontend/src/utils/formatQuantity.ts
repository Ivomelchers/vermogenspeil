export function formatQuantity(value: string | number): string {
  const amount = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(amount) || amount === 0) return "0";

  const abs = Math.abs(amount);
  let maxDecimals = 8;

  if (abs > 0 && abs < 1) {
    // Show enough decimals to expose at least 4 significant digits
    const magnitude = Math.floor(Math.log10(abs));
    maxDecimals = Math.min(Math.max(-magnitude + 3, 8), 12);
  }

  return new Intl.NumberFormat("nl-NL", {
    maximumFractionDigits: maxDecimals,
    minimumFractionDigits: 0,
  }).format(amount);
}
