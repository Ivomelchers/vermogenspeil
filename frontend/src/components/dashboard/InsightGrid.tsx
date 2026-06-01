import { SimpleGrid } from "@chakra-ui/react";

import type { DashboardSummary } from "../../api/portfolio";
import InsightCard from "../common/InsightCard";
import { formatEur } from "../../utils/formatMoney";

interface InsightGridProps {
  summary: DashboardSummary;
}

export default function InsightGrid({ summary }: InsightGridProps) {
  const returns = summary.returns;
  const invested = parseFloat(returns?.invested_eur ?? "0");
  const unrealized = parseFloat(returns?.unrealized_return_eur ?? "0");
  const unrealizedPct = returns?.unrealized_return_percent ?? "0";
  const total = summary.total_value_eur;

  if (invested <= 0 && !summary.ytd?.available) {
    return null;
  }

  return (
    <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={4}>
      {invested > 0 && (
        <InsightCard
          label="Totaal ingelegd"
          value={formatEur(returns!.invested_eur)}
          delta="cost basis · alle aankopen"
          accent="ochre"
        />
      )}
      <InsightCard
        label="Huidige waarde"
        value={formatEur(total)}
        delta={new Date().toLocaleDateString("nl-NL", {
          day: "numeric",
          month: "long",
          year: "numeric",
        })}
      />
      {invested > 0 && (
        <InsightCard
          label={unrealized >= 0 ? "Totale winst" : "Totaal verlies"}
          value={formatEur(returns!.unrealized_return_eur)}
          delta={`${unrealized >= 0 ? "+" : ""}${unrealizedPct}% onrealiseerd`}
          tone={unrealized >= 0 ? "positive" : "negative"}
        />
      )}
      {summary.ytd?.available && (
        <InsightCard
          label={`Rendement YTD ${summary.ytd.year}`}
          value={`${parseFloat(summary.ytd.ytd_return_eur ?? "0") >= 0 ? "+" : ""}${formatEur(summary.ytd.ytd_return_eur ?? "0")}`}
          delta={`${summary.ytd.ytd_return_percent}% t.o.v. peildatum`}
          tone={
            parseFloat(summary.ytd.ytd_return_eur ?? "0") >= 0 ? "positive" : "negative"
          }
        />
      )}
    </SimpleGrid>
  );
}
