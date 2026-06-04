import { Box, Flex, Text, Tooltip } from "@chakra-ui/react";

import type { DashboardPosition } from "../../api/portfolio";
import { formatEur } from "../../utils/formatMoney";

interface PositionPnLTableProps {
  dashboardPositions: DashboardPosition[];
}

function parseNum(v: string | null | undefined): number {
  if (!v) return 0;
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : 0;
}

export default function PositionPnLTable({
  dashboardPositions,
}: PositionPnLTableProps) {
  const rows = dashboardPositions
    .map((pos) => {
      const value = parseNum(pos.value_eur);
      const invested = parseNum(pos.cost_basis_eur);
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
          align="center"
        >
          <Box flex={2}>Asset</Box>
          <Box flex={1} textAlign="right">
            <Tooltip
              label="Aantal × gemiddelde aankoopprijs per stuk (incl. kosten uit uw import)."
              placement="top"
              hasArrow
            >
              <Box as="span" borderBottom="1px dotted" borderColor="ink.faint" cursor="help">
                Kostprijs
              </Box>
            </Tooltip>
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
