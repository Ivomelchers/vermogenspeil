/** Nederlandse datum voor "waarden per …" in belasting-UI. */
export function formatReferenceDate(date: Date = new Date()): string {
  return new Intl.DateTimeFormat("nl-NL", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(date);
}

export function werkelijkReferenceLabel(date: Date = new Date()): string {
  return `Gebaseerd op waarden per ${formatReferenceDate(date)} (start: peildatum 1 jan, einde: huidige portefeuille).`;
}
