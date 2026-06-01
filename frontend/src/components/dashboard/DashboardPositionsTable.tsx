import { Box, Flex, Link, Table, Tbody, Td, Text, Th, Thead, Tr } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import type { DashboardPosition } from "../../api/portfolio";
import { formatEur } from "../../utils/formatMoney";
import { positionPriceHint } from "../../utils/valuationLabels";

interface DashboardPositionsTableProps {
  positions: DashboardPosition[];
  totalCount: number;
}

export default function DashboardPositionsTable({
  positions,
  totalCount,
}: DashboardPositionsTableProps) {
  if (positions.length === 0) {
    return (
      <Text fontSize="sm" color="ink.dim">
        Geen posities.
      </Text>
    );
  }

  return (
    <Box>
      <Box
        maxH="240px"
        overflowY="auto"
        border="1px solid"
        borderColor="line.soft"
        borderRadius="base"
        bg="paper"
      >
        <Table size="sm" variant="simple">
          <Thead position="sticky" top={0} bg="backgroundCard" zIndex={1}>
            <Tr>
              <Th
                py={2}
                px={3}
                fontSize="kicker"
                letterSpacing="0.1em"
                textTransform="uppercase"
                color="taupe.500"
                borderColor="line.soft"
              >
                Asset
              </Th>
              <Th
                py={2}
                px={3}
                isNumeric
                fontSize="kicker"
                letterSpacing="0.1em"
                textTransform="uppercase"
                color="taupe.500"
                borderColor="line.soft"
              >
                Waarde
              </Th>
            </Tr>
          </Thead>
          <Tbody>
            {positions.slice(0, 8).map((position) => {
              const hint = positionPriceHint(position);
              return (
                <Tr key={position.id} _hover={{ bg: "azure.50" }}>
                  <Td py={2.5} px={3} borderColor="line.soft">
                    <Text fontWeight={600} fontSize="sm">
                      {position.symbol}
                    </Text>
                    <Text fontSize="xs" color="taupe.500">
                      {position.category_label}
                      {hint ? ` · ${hint}` : ""}
                    </Text>
                  </Td>
                  <Td py={2.5} px={3} isNumeric borderColor="line.soft">
                    <Text fontWeight={500} fontSize="sm">
                      {formatEur(position.value_eur)}
                    </Text>
                    <Text fontSize="xs" color="taupe.500">
                      {position.quantity} st.
                    </Text>
                  </Td>
                </Tr>
              );
            })}
          </Tbody>
        </Table>
      </Box>
      {totalCount > 8 && (
        <Flex justify="flex-end" mt={2}>
          <Link as={RouterLink} to="/portfolio" fontSize="sm" color="azure.500">
            Alle {totalCount} posities →
          </Link>
        </Flex>
      )}
    </Box>
  );
}
