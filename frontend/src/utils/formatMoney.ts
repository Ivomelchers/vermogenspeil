export function formatEurParts(value: string | number): { whole: string; fraction: string } {
  const amount = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(amount)) {
    return { whole: "0", fraction: "00" };
  }

  const formatted = new Intl.NumberFormat("nl-NL", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);

  const [whole, fraction = "00"] = formatted.split(",");
  return { whole, fraction };
}

export function formatEur(value: string | number): string {
  const amount = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(amount)) {
    return "€ 0,00";
  }
  return new Intl.NumberFormat("nl-NL", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

export function formatDateNl(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString("nl-NL", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
