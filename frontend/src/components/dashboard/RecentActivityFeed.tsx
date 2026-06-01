import { Box, Flex, Text, VStack } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import type { DashboardActivity } from "../../api/portfolio";
import { formatDateNl, formatEur } from "../../utils/formatMoney";
import { platformLabel } from "../../utils/platformLabels";

interface RecentActivityFeedProps {
  items: DashboardActivity[];
}

export default function RecentActivityFeed({ items }: RecentActivityFeedProps) {
  if (items.length === 0) {
    return (
      <Text fontSize="sm" color="ink.dim" lineHeight={1.6}>
        Nog geen transacties.{" "}
        <Box as={RouterLink} to="/portfolio/manual/transaction" color="azure.500">
          Voeg een transactie toe
        </Box>
      </Text>
    );
  }

  return (
    <Box
      maxH="240px"
      overflowY="auto"
      border="1px solid"
      borderColor="line.soft"
      borderRadius="base"
      bg="paper"
    >
      <VStack align="stretch" spacing={0} divider={<Box borderColor="line.soft" borderTopWidth="1px" />}>
        {items.slice(0, 6).map((item) => (
          <Flex key={item.id} px={3} py={2.5} justify="space-between" gap={2} _hover={{ bg: "azure.50" }}>
            <Box minW={0}>
              <Text fontWeight={600} fontSize="sm" noOfLines={1}>
                {item.symbol}
              </Text>
              <Text fontSize="xs" color="taupe.500" noOfLines={1}>
                {item.transaction_type_label} · {platformLabel(item.source_platform)}
              </Text>
            </Box>
            <Box textAlign="right" flexShrink={0}>
              {item.total_eur && (
                <Text fontWeight={500} fontSize="sm">
                  {formatEur(item.total_eur)}
                </Text>
              )}
              <Text fontSize="xs" color="taupe.500">
                {formatDateNl(item.occurred_at)}
              </Text>
            </Box>
          </Flex>
        ))}
      </VStack>
    </Box>
  );
}
