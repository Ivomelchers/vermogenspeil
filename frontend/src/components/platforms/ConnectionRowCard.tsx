import { memo } from "react";
import { Box, Button, Flex, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";

import type { PlatformConnection } from "../../api/integrations";
import { getCatalogPlatform } from "../../data/platformCatalog";
import { staggerItem } from "../layout/motion";
import PlatformAvatar from "./PlatformAvatar";
import ImportHistoryPanel from "./ImportHistoryPanel";

function relativeSync(value: string | null): string {
  if (!value) return "Nog niet gesynchroniseerd";
  const d = new Date(value);
  const diffMin = Math.floor((Date.now() - d.getTime()) / 60000);
  if (diffMin < 1) return "Zojuist gesynchroniseerd";
  if (diffMin < 60) return `${diffMin} min geleden gesynchroniseerd`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 48) return `${diffH} uur geleden gesynchroniseerd`;
  const diffD = Math.floor(diffH / 24);
  return `Laatste upload ${diffD} dag${diffD === 1 ? "" : "en"} geleden`;
}

function statusDot(status: PlatformConnection["status"]): string {
  if (status === "success") return "moss.500";
  if (status === "error") return "rust.500";
  return "ochre.500";
}

interface ConnectionRowCardProps {
  connection: PlatformConnection;
  secondaryLine?: string;
  syncing?: boolean;
  onSync?: () => void;
  onManage?: () => void;
  onDisconnect?: () => void;
  onPurgeData?: () => void;
  primaryActionLabel?: string;
  showImportHistory?: boolean;
  onImportHistoryChanged?: () => void;
}

function ConnectionRowCardComponent({
  connection,
  secondaryLine,
  syncing,
  onSync,
  onManage,
  onDisconnect,
  onPurgeData,
  primaryActionLabel,
  showImportHistory = true,
  onImportHistoryChanged,
}: ConnectionRowCardProps) {
  const catalog = getCatalogPlatform(connection.platform);
  const initials =
    catalog?.initials ??
    connection.display_name.slice(0, 2);
  const color = catalog?.color ?? "#2d5a3a";
  const isCsv = connection.connection_method === "csv";

  return (
    <motion.div variants={staggerItem}>
      <Box
        p={4}
        bg="backgroundCard"
        border="1px solid"
        borderColor="line.soft"
        borderRadius="base"
        transition="all 0.2s ease"
        _hover={{
          borderColor: "azure.300",
          boxShadow: "0 6px 24px rgba(26, 58, 92, 0.07)",
        }}
      >
        <Flex
          gap={4}
          align={{ base: "stretch", md: "center" }}
          direction={{ base: "column", md: "row" }}
        >
          <PlatformAvatar initials={initials} color={color} />
          <Box flex={1} minW={0}>
            <Text fontFamily="heading" fontSize="lg" fontWeight={500} letterSpacing="-0.02em">
              {connection.display_name}
            </Text>
            <Text fontSize="sm" color="ink.dim" mt={1}>
              {connection.platform_display} · {connection.connection_method_display}
              {connection.connection_method === "api" && " · view-only API-key"}
            </Text>
          </Box>
          <Flex align="center" gap={3} minW={{ md: "220px" }}>
            <Box w="8px" h="8px" borderRadius="full" bg={statusDot(connection.status)} flexShrink={0} />
            <Box flex={1}>
              <Text fontSize="sm" fontWeight={500}>
                {relativeSync(connection.last_synced_at)}
              </Text>
              {secondaryLine && (
                <Text fontSize="sm" color="ink.dim">
                  {secondaryLine}
                </Text>
              )}
              {connection.last_error && (
                <Text fontSize="sm" color="rust.500" mt={1}>
                  {connection.last_error}
                </Text>
              )}
            </Box>
          </Flex>
          <Flex gap={2} flexWrap="wrap">
            {!isCsv && onSync && (
              <Button
                variant="fiscalOutline"
                size="sm"
                isLoading={syncing}
                onClick={onSync}
              >
                Synchroniseren
              </Button>
            )}
            {isCsv && onManage && (
              <Button variant="fiscal" size="sm" onClick={onManage}>
                {primaryActionLabel ?? "↺ Recentere upload"}
              </Button>
            )}
            {onManage && !isCsv && (
              <Button variant="fiscalOutline" size="sm" onClick={onManage}>
                Beheren
              </Button>
            )}
            {onDisconnect && (
              <Button variant="fiscalOutline" size="sm" onClick={onDisconnect}>
                Loskoppelen
              </Button>
            )}
            {onPurgeData && (
              <Button
                variant="fiscalOutline"
                size="sm"
                color="rust.500"
                onClick={onPurgeData}
              >
                Alle data wissen
              </Button>
            )}
          </Flex>
        </Flex>
        {showImportHistory && (
          <ImportHistoryPanel
            connection={connection}
            onChanged={onImportHistoryChanged}
          />
        )}
      </Box>
    </motion.div>
  );
}

export default memo(ConnectionRowCardComponent);
