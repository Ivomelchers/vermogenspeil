import { Box, Flex, Text } from "@chakra-ui/react";

import type { DashboardPosition } from "../../api/portfolio";
import type { Position } from "../../api/portfolio";
import { formatEur } from "../../utils/formatMoney";

interface PositionPnLTableProps {
  dashboardPositions: DashboardPosition[];
  detailPositions: Position[];
}

function parseNum(v: string | null | undefined): number {
  if (!v) return 0;
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : 0;
}

export default function PositionPnLTable({
  dashboardPositions,
  detailPositions,
}: PositionPnLTableProps) {
  const costByAssetId = new Map(
    detailPositions.map((p) => [p.asset.id, parseNum(p.average_cost_eur)]),
  );

  const rows = dashboardPositions
    .map((pos) => {
      const qty = parseNum(pos.quantity);
      const value = parseNum(pos.value_eur);
      const avgCost = pos.asset_id != null ? costByAssetId.get(pos.asset_id) ?? 0 : 0;
      const invested = qty * avgCost;
      const pnl = value - invested;
      const pct = invested > 0 ? (pnl / invested) * 100 : 0;
      return { pos, invested, value, pnl, pct, hasCost: invested > 0 };
    })
    .filter((r) => r.hasCost)
    .sort((a, b) => b.pnl - a.pnl);

  if (rows.length === 0) {
    return (
      <Text fontSize="sm" color="ink.dim" fontStyle="italic">
        Voeg transacties met aankoopprijs toe om winst/verlies per positie te zien.
      </Text>
    );
  }

  return (
    <Box overflowX="auto">
      <Box minW="640px">
        <Flex
          py={2}
          px={3}
          borderBottom="2px solid"
          borderColor="line.DEFAULT"
          fontSize="10px"
          letterSpacing="0.12em"
          textTransform="uppercase"
          color="ink.faint"
          fontWeight={600}
          gap={2}
        >
          <Box flex={2}>Asset</Box>
          <Box flex={1} textAlign="right">
            Inleg
          </Box>
          <Box flex={1} textAlign="right">
            Huidige waarde
          </Box>
          <Box flex={1} textAlign="right">
            Winst / verlies
          </Box>
          <Box w="56px" textAlign="right">
            %
          </Box>
        </Flex>
        {rows.map(({ pos, invested, pnl, pct }) => (
          <Flex
            key={pos.id}
            py={3}
            px={3}
            gap={2}
            borderBottom="1px solid"
            borderColor="line.soft"
            align="center"
            _hover={{ bg: "azure.50" }}
            transition="background 0.15s"
          >
            <Box flex={2}>
              <Text fontWeight={600}>{pos.symbol}</Text>
              <Text fontSize="xs" color="ink.dim">
                {pos.name}
              </Text>
            </Box>
            <Box flex={1} textAlign="right" fontSize="sm">
              {formatEur(String(invested))}
            </Box>
            <Box flex={1} textAlign="right" fontSize="sm">
              {formatEur(pos.value_eur)}
            </Box>
            <Box
              flex={1}
              textAlign="right"
              fontSize="sm"
              fontWeight={600}
              color={pnl >= 0 ? "moss.500" : "rust.500"}
            >
              {pnl >= 0 ? "+" : ""}
              {formatEur(String(Math.abs(pnl)))}
            </Box>
            <Box
              w="56px"
              textAlign="right"
              fontSize="sm"
              color={pct >= 0 ? "moss.500" : "rust.500"}
            >
              {pct >= 0 ? "+" : ""}
              {pct.toFixed(1)}%
            </Box>
          </Flex>
        ))}
      </Box>
    </Box>
  );
}
