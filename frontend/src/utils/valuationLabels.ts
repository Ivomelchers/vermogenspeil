import type { DashboardPosition, DashboardSummary } from "../api/portfolio";
import { formatEur } from "./formatMoney";

export function valuationBasisLabel(
  method: DashboardSummary["valuation_method"] | undefined,
): string {
  switch (method) {
    case "market":
      return "Marktwaarde";
    case "mixed":
      return "Deels marktwaarde";
    default:
      return "Kostprijs";
  }
}

export function returnBasisLabel(method: string | undefined): string {
  switch (method) {
    case "market":
      return "t.o.v. inleg (marktwaarde)";
    case "mixed":
      return "t.o.v. inleg (deels markt)";
    default:
      return "t.o.v. inleg";
  }
}

export function positionPriceHint(position: DashboardPosition): string | null {
  if (position.valuation_source === "market" && position.unit_price_eur) {
    const sourceLabel =
      position.price_source === "bitvavo"
        ? "Bitvavo"
        : position.price_source === "yahoo"
          ? "Yahoo"
          : "live koers";
    return `${formatEur(position.unit_price_eur)} / st. · ${sourceLabel}`;
  }
  if (position.valuation_source === "cost_basis") {
    return "Waarde op kostprijs";
  }
  return null;
}
