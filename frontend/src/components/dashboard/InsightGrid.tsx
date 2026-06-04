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

  if (costBasis <= 0 && !summary.ytd?.available) {
    return null;
  }

  const trust = summary.metrics_trust;
  const showCostBasis = costBasis > 0 && (trust?.invested_trusted ?? true);
  const ytdTrusted = summary.ytd?.trusted !== false && (trust?.ytd_trusted ?? true);
  const showBuyOutflowFootnote =
    buyOutflow > 0 && Math.abs(buyOutflow - costBasis) > 0.01;

  return (
    <Box>
      {trust?.has_warnings && (
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
          {trust.missing_price_symbols && trust.missing_price_symbols.length > 0 && (
            <Text fontSize="xs" color="ink.faint" mt={1}>
              Symbolen zonder live koers: {trust.missing_price_symbols.join(", ")}
            </Text>
          )}
        </Box>
      )}
      {returns?.note && (
        <Text fontSize="xs" color="ink.dim" mb={3} lineHeight={1.5}>
          {returns.note}
        </Text>
      )}
      <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={4}>
        {showCostBasis && (
          <InsightCard
            label="Kostprijs portefeuille"
            value={formatEur(returns!.invested_eur)}
            delta="huidige posities · incl. aankoopkosten"
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
          <InsightCard
            label={unrealized >= 0 ? "Onrealiseerde winst" : "Onrealiseerd verlies"}
            value={formatEur(returns!.unrealized_return_eur)}
            delta={`${unrealized >= 0 ? "+" : ""}${unrealizedPct}% t.o.v. kostprijs`}
            tone={unrealized >= 0 ? "positive" : "negative"}
          />
        )}
        {summary.ytd?.available && (
          <InsightCard
            label={`Rendement YTD ${summary.ytd.year}${ytdTrusted ? "" : " (indicatief)"}`}
            value={`${parseFloat(summary.ytd.ytd_return_eur ?? "0") >= 0 ? "+" : ""}${formatEur(summary.ytd.ytd_return_eur ?? "0")}`}
            delta={
              ytdTrusted
                ? `${summary.ytd.ytd_return_percent}% t.o.v. start dit jaar`
                : "wacht op betrouwbare koersen"
            }
            tone={
              parseFloat(summary.ytd.ytd_return_eur ?? "0") >= 0 ? "positive" : "negative"
            }
          />
        )}
      </SimpleGrid>
      {showBuyOutflowFootnote && (
        <Text fontSize="xs" color="ink.faint" mt={3}>
          Totaal aan aankopen (historisch, incl. verkochte stuks):{" "}
          {formatEur(returns!.total_buy_outflow_eur!)}
        </Text>
      )}
    </Box>
  );
}
