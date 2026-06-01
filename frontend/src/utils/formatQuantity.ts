export function formatQuantity(value: string | number): string {
  const amount = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(amount)) {
    return "0";
  }
  return new Intl.NumberFormat("nl-NL", {
    maximumFractionDigits: 8,
    minimumFractionDigits: 0,
  }).format(amount);
}
