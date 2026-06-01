import { Box, Flex, Text, VStack } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import type { DashboardPlatform } from "../../api/portfolio";
import Kicker from "../common/Kicker";

const STATUS_COLORS: Record<string, string> = {
  success: "moss.500",
  running: "azure.500",
  error: "rust.500",
  pending: "taupe.500",
};

function statusColor(status: string): string {
  return STATUS_COLORS[status.toLowerCase()] ?? "taupe.500";
}

interface PlatformStripProps {
  platforms: DashboardPlatform[];
}

export default function PlatformStrip({ platforms }: PlatformStripProps) {
  if (platforms.length === 0) return null;

  return (
    <VStack align="stretch" spacing={2}>
      {platforms.map((platform) => (
        <Flex
          key={platform.id}
          as={RouterLink}
          to="/platforms"
          align="center"
          justify="space-between"
          gap={3}
          px={4}
          py={3}
          bg="paper"
          border="1px solid"
          borderColor="line.soft"
          borderRadius="base"
          transition="border-color 0.15s ease, background 0.15s ease"
          _hover={{
            borderColor: "azure.300",
            bg: "azure.50",
            textDecoration: "none",
          }}
        >
          <Box minW={0}>
            <Text fontWeight={600} fontSize="sm" noOfLines={1}>
              {platform.display_name}
            </Text>
            <Kicker mt={0.5} fontSize="9px">
              {platform.platform_display}
            </Kicker>
          </Box>
          <Flex align="center" gap={2} flexShrink={0}>
            <Box w="6px" h="6px" borderRadius="full" bg={statusColor(platform.status)} />
            <Text fontSize="xs" color="ink.dim" textTransform="capitalize">
              {platform.status}
            </Text>
          </Flex>
        </Flex>
      ))}
    </VStack>
  );
}
