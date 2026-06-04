import { Box, SimpleGrid, Text } from "@chakra-ui/react";

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

  const trust = summary.metrics_trust;
  const showInvested = invested > 0 && (trust?.invested_trusted ?? true);
  const ytdTrusted = summary.ytd?.trusted !== false && (trust?.ytd_trusted ?? true);

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
    <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={4}>
      {showInvested && (
        <InsightCard
          label="Totaal ingelegd"
          value={formatEur(returns!.invested_eur)}
          delta="alle kooptransacties (incl. kosten)"
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
    </Box>
  );
}
