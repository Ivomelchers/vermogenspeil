import { Box, SimpleGrid } from "@chakra-ui/react";

import type { DashboardSummary } from "../../api/portfolio";
import InsightCard from "../common/InsightCard";
import { formatEur } from "../../utils/formatMoney";

interface InsightGridProps {
  summary: DashboardSummary;
}

export default function InsightGrid({ summary }: InsightGridProps) {
  const returns = summary.returns;
  const costBasis = parseFloat(
    returns?.cost_basis_eur ?? returns?.invested_eur ?? "0",
  );
  const unrealized = parseFloat(returns?.unrealized_return_eur ?? "0");
  const unrealizedPct = returns?.unrealized_return_percent ?? "0";
  const total = summary.total_value_eur;

  if (costBasis <= 0 && !summary.ytd?.available) {
    return null;
  }

  const trust = summary.metrics_trust;
  const showInleg = costBasis > 0 && (trust?.invested_trusted ?? true);
  const ytdEur = parseFloat(summary.ytd?.ytd_return_eur ?? "0");

  return (
    <Box>
      <SimpleGrid columns={{ base: 1, sm: 2, lg: 3, xl: 6 }} spacing={4}>
        {showInleg && (
          <InsightCard
            label="Totale inleg"
            value={formatEur(returns!.cost_basis_eur ?? returns!.invested_eur)}
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
        {costBasis > 0 && (
          <>
            <InsightCard
              label={unrealized >= 0 ? "Winst" : "Verlies"}
              value={formatEur(returns!.unrealized_return_eur)}
              tone={unrealized >= 0 ? "positive" : "negative"}
            />
            <InsightCard
              label="Rendement"
              value={`${unrealized >= 0 ? "+" : ""}${unrealizedPct}%`}
              delta="Op uw totale inleg"
              tone={unrealized >= 0 ? "positive" : "negative"}
            />
          </>
        )}
        {summary.ytd?.available && (
          <InsightCard
            label={`Rendement dit jaar (${summary.ytd.year})`}
            value={`${ytdEur >= 0 ? "+" : ""}${formatEur(summary.ytd.ytd_return_eur ?? "0")}`}
            delta={`${summary.ytd.ytd_return_percent}% sinds 1 januari`}
            tone={ytdEur >= 0 ? "positive" : "negative"}
          />
        )}
      </SimpleGrid>
    </Box>
  );
}
