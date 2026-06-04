import { Box, SimpleGrid, Text } from "@chakra-ui/react";

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
  const buyOutflow = parseFloat(returns?.total_buy_outflow_eur ?? "0");
  const unrealized = parseFloat(returns?.unrealized_return_eur ?? "0");
  const unrealizedPct = returns?.unrealized_return_percent ?? "0";
  const total = summary.total_value_eur;

  if (costBasis <= 0 && buyOutflow <= 0 && !summary.ytd?.available) {
    return null;
  }

  const trust = summary.metrics_trust;
  const showBuyOutflow = buyOutflow > 0 && (trust?.invested_trusted ?? true);
  const showCostBasis = costBasis > 0 && (trust?.invested_trusted ?? true);
  const ytdTrusted = summary.ytd?.trusted !== false && (trust?.ytd_trusted ?? true);
  const metricsDiffer = Math.abs(buyOutflow - costBasis) > 0.01;

  return (
    <Box>
      {trust?.has_warnings && trust.warnings.length > 0 && (
        <Box
          mb={4}
          p={3}
          borderRadius="base"
          border="1px solid"
          borderColor="ochre.200"
          bg="ochre.50"
        >
          {trust.warnings.map((w) => (
            <Text
              key={w}
              fontSize="sm"
              color="ink.primary"
              mb={trust.warnings.length > 1 ? 1 : 0}
            >
              {w}
            </Text>
          ))}
        </Box>
      )}

      {metricsDiffer && (
        <Text fontSize="sm" color="ink.dim" mb={3} lineHeight={1.5}>
          U heeft (deels) verkocht: &lsquo;ingelegd nu&rsquo; is lager dan &lsquo;alle
          aankopen&rsquo;.
        </Text>
      )}

      <SimpleGrid columns={{ base: 1, sm: 2, xl: 5 }} spacing={4}>
        {showBuyOutflow && (
          <InsightCard
            label="Alle aankopen"
            value={formatEur(returns!.total_buy_outflow_eur ?? returns!.invested_eur)}
            delta="Som van al uw koopregels, incl. kosten per koop"
            accent="ochre"
          />
        )}
        {showCostBasis && (
          <InsightCard
            label="Ingelegd nu"
            value={formatEur(returns!.cost_basis_eur ?? returns!.invested_eur)}
            delta={
              metricsDiffer ? "Wat uw huidige posities kosten" : "U heeft nog niets verkocht"
            }
          />
        )}
        <InsightCard
          label="Waarde nu"
          value={formatEur(total)}
          delta={new Date().toLocaleDateString("nl-NL", {
            day: "numeric",
            month: "long",
            year: "numeric",
          })}
        />
        {costBasis > 0 && (
          <InsightCard
            label={unrealized >= 0 ? "Winst" : "Verlies"}
            value={formatEur(returns!.unrealized_return_eur)}
            delta={`${unrealized >= 0 ? "+" : ""}${unrealizedPct}% op ingelegd nu`}
            tone={unrealized >= 0 ? "positive" : "negative"}
          />
        )}
        {summary.ytd?.available && (
          <InsightCard
            label={`Dit jaar (${summary.ytd.year})${ytdTrusted ? "" : " · indicatief"}`}
            value={`${parseFloat(summary.ytd.ytd_return_eur ?? "0") >= 0 ? "+" : ""}${formatEur(summary.ytd.ytd_return_eur ?? "0")}`}
            delta={
              ytdTrusted
                ? `${summary.ytd.ytd_return_percent}% sinds 1 januari`
                : "Nog niet alle koersen beschikbaar"
            }
            tone={
              parseFloat(summary.ytd.ytd_return_eur ?? "0") >= 0 ? "positive" : "negative"
            }
          />
        )}
      </SimpleGrid>
    </Box>
  );
}
