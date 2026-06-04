import type { DashboardPosition } from "../api/portfolio";
import { formatEur } from "./formatMoney";

export function positionPriceHint(position: DashboardPosition): string | null {
  if (position.valuation_source === "market" && position.unit_price_eur) {
    return formatEur(position.unit_price_eur);
  }
  return null;
}
