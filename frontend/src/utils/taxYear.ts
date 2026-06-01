/**
 * Relevant belastingjaar (Europe/Amsterdam, deadline 1 mei).
 * Moet gelijk lopen met backend apps.tax.services.tax_year.
 */
export function relevantTaxYear(date: Date = new Date()): number {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Amsterdam",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const parts = formatter.formatToParts(date);
  const year = Number(parts.find((p) => p.type === "year")?.value ?? date.getFullYear());
  const month = Number(parts.find((p) => p.type === "month")?.value ?? 1);
  const day = Number(parts.find((p) => p.type === "day")?.value ?? 1);

  if (month < 5 || (month === 5 && day < 1)) {
    return year - 1;
  }
  return year;
}

export function displayTaxYear(userActiveTaxYear?: number): number {
  const relevant = relevantTaxYear();
  if (!userActiveTaxYear) {
    return relevant;
  }
  return userActiveTaxYear;
}
