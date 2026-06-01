import { Badge, Box, Button, Flex, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";

import type { PlatformConnection, SyncStatus } from "../../api/integrations";
import FiscalCard from "../common/FiscalCard";
import Kicker from "../common/Kicker";
import { staggerItem } from "../layout/motion";

function statusBadgeProps(status: SyncStatus): {
  label: string;
  colorScheme: string;
} {
  switch (status) {
    case "success":
      return { label: "Gesynchroniseerd", colorScheme: "green" };
    case "running":
    case "pending":
      return { label: "Synchroniseren…", colorScheme: "yellow" };
    case "error":
      return { label: "Fout", colorScheme: "red" };
    default:
      return { label: status, colorScheme: "gray" };
  }
}

function formatSyncedAt(value: string | null): string {
  if (!value) return "Nog niet gesynchroniseerd";
  return new Date(value).toLocaleString("nl-NL", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

interface PlatformConnectionCardProps {
  connection: PlatformConnection;
  syncing: boolean;
  emailVerified: boolean;
  onSync: () => void;
  onDelete: () => void;
}

export default function PlatformConnectionCard({
  connection,
  syncing,
  emailVerified,
  onSync,
  onDelete,
}: PlatformConnectionCardProps) {
  const badge = statusBadgeProps(connection.status);

  return (
    <motion.div variants={staggerItem} whileHover={{ y: -2 }} transition={{ duration: 0.2 }}>
      <FiscalCard
        elevated
        p={5}
        sx={{
          transition: "box-shadow 0.25s ease, border-color 0.25s ease",
          _hover: {
            borderColor: "azure.300",
            boxShadow: "0 8px 32px rgba(26, 58, 92, 0.08)",
          },
        }}
      >
        <Flex
          justify="space-between"
          align={{ base: "stretch", md: "center" }}
          gap={4}
          direction={{ base: "column", md: "row" }}
        >
          <Box>
            <Flex align="center" gap={2} mb={2} flexWrap="wrap">
              <Text
                fontFamily="heading"
                fontSize="lg"
                fontWeight={500}
                letterSpacing="-0.02em"
              >
                {connection.display_name}
              </Text>
              <Badge
                colorScheme={badge.colorScheme}
                variant="subtle"
                fontSize="10px"
                textTransform="uppercase"
                letterSpacing="0.08em"
              >
                {badge.label}
              </Badge>
            </Flex>
            <Kicker>
              {connection.connection_method_display} · {connection.platform_display}
            </Kicker>
            <Text fontSize="sm" color="ink.dim" mt={3}>
              {formatSyncedAt(connection.last_synced_at)}
            </Text>
            {connection.connection_method === "csv" && (
              <Text fontSize="sm" color="taupe.500" mt={1}>
                Bijwerken via een nieuwe CSV-upload.
              </Text>
            )}
            {connection.last_error && (
              <Text fontSize="sm" color="rust.500" mt={2}>
                {connection.last_error}
              </Text>
            )}
          </Box>

          <Flex gap={2} flexWrap="wrap" alignSelf={{ base: "flex-start", md: "center" }}>
            {connection.connection_method !== "csv" && (
              <Button
                variant="fiscalOutline"
                size="sm"
                isLoading={syncing}
                onClick={onSync}
                isDisabled={!emailVerified}
              >
                Synchroniseren
              </Button>
            )}
            <Button
              variant="fiscalOutline"
              size="sm"
              color="rust.500"
              borderColor="line.DEFAULT"
              _hover={{ borderColor: "rust.500", bg: "rust.50" }}
              onClick={onDelete}
            >
              Verwijderen
            </Button>
          </Flex>
        </Flex>
      </FiscalCard>
    </motion.div>
  );
}
