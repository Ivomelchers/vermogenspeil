import { useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import {
  Badge,
  Box,
  Button,
  Flex,
  Heading,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import {
  deleteConnection,
  getDemoFeaturesEnabled,
  listConnections,
  pollSyncJob,
  seedDemoPortfolio,
  triggerSync,
  type PlatformConnection,
  type SyncStatus,
} from "../api/integrations";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { useUser } from "../contexts/UserContext";
import { getApiErrorMessage } from "../utils/apiError";

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

export default function PlatformsPage() {
  const { user } = useUser();
  const location = useLocation();
  const [connections, setConnections] = useState<PlatformConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState(
    (location.state as { message?: string } | null)?.message ?? "",
  );
  const [syncingId, setSyncingId] = useState<number | null>(null);
  const [demoEnabled, setDemoEnabled] = useState(false);
  const [isSeedingDemo, setIsSeedingDemo] = useState(false);

  useEffect(() => {
    void getDemoFeaturesEnabled()
      .then(setDemoEnabled)
      .catch(() => setDemoEnabled(false));
  }, []);

  const loadConnections = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await listConnections();
      setConnections(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Platformen laden mislukt."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadConnections();
  }, [loadConnections]);

  async function handleSync(connection: PlatformConnection) {
    setError("");
    setMessage("");
    setSyncingId(connection.id);
    try {
      const job = await triggerSync(connection.id);
      const result = await pollSyncJob(job.id);
      if (result.status === "error") {
        setError(result.error_message || "Synchronisatie mislukt.");
      } else {
        setMessage(
          `Synchronisatie voltooid: ${result.positions_synced} posities, ${result.transactions_synced} transacties.`,
        );
      }
      await loadConnections();
    } catch (syncError) {
      setError(getApiErrorMessage(syncError, "Synchronisatie mislukt."));
    } finally {
      setSyncingId(null);
    }
  }

  async function handleSeedDemo() {
    setError("");
    setMessage("");
    setIsSeedingDemo(true);
    try {
      const result = await seedDemoPortfolio();
      setMessage(
        `Voorbeelddata geladen: ${result.connections.length} platformen, ` +
          `${result.positions_synced} posities, ${result.transactions_synced} transacties.`,
      );
      await loadConnections();
    } catch (seedError) {
      setError(getApiErrorMessage(seedError, "Voorbeelddata laden mislukt."));
    } finally {
      setIsSeedingDemo(false);
    }
  }

  async function handleDelete(connection: PlatformConnection) {
    if (!window.confirm(`Weet u zeker dat u ${connection.display_name} wilt verwijderen?`)) {
      return;
    }
    setError("");
    setMessage("");
    try {
      await deleteConnection(connection.id);
      setMessage(`${connection.display_name} is verwijderd.`);
      await loadConnections();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Verwijderen mislukt."));
    }
  }

  return (
    <VStack align="stretch" spacing={8} maxW="3xl">
      <Box>
        <Kicker mb={2}>Platformen</Kicker>
        <Heading size="lg">Mijn platformen</Heading>
        <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
          Koppel brokers en exchanges om uw vermogen automatisch bij te werken.
          Alleen-lezen API-keys worden versleuteld opgeslagen.
        </Text>
      </Box>

      {user && !user.email_verified && (
        <AuthAlert tone="info">
          Bevestig eerst uw e-mailadres voordat u een platform kunt koppelen.
        </AuthAlert>
      )}

      {error && <AuthAlert tone="error">{error}</AuthAlert>}
      {message && <AuthAlert tone="success">{message}</AuthAlert>}

      {demoEnabled && (
        <FiscalCard p={5} borderLeft="3px solid" borderLeftColor="gold.500" bg="gold.50">
          <Kicker mb={2} color="gold.600">
            Ontwikkeling · voorbeelddata
          </Kicker>
          <Text fontSize="sm" color="ink.dim" lineHeight={1.7} mb={4}>
            Laad een fictieve Bitvavo- en DEGIRO-koppeling met posities en transacties.
            Geen broker-accounts of API-keys nodig — alleen lokaal beschikbaar.
          </Text>
          <Button
            variant="fiscal"
            isLoading={isSeedingDemo}
            loadingText="Laden…"
            onClick={() => void handleSeedDemo()}
          >
            Laad voorbeeldportefeuille
          </Button>
        </FiscalCard>
      )}

      <Flex gap={3} flexWrap="wrap">
        <Button
          as={RouterLink}
          to="/platforms/add"
          variant="fiscal"
          isDisabled={!user?.email_verified}
        >
          Platform toevoegen
        </Button>
      </Flex>

      {loading ? (
        <Text color="ink.dim" fontSize="sm">
          Platformen laden…
        </Text>
      ) : connections.length === 0 ? (
        <FiscalCard p={6}>
          <Text fontFamily="heading" fontStyle="italic" color="ink.dim" lineHeight={1.7}>
            U heeft nog geen platformen gekoppeld. Begin met Bitvavo via API voor
            automatische crypto-synchronisatie.
          </Text>
        </FiscalCard>
      ) : (
        <VStack align="stretch" spacing={3}>
          {connections.map((connection) => {
            const badge = statusBadgeProps(connection.status);
            return (
              <FiscalCard key={connection.id} p={5}>
                <Flex
                  justify="space-between"
                  align={{ base: "stretch", md: "center" }}
                  gap={4}
                  direction={{ base: "column", md: "row" }}
                >
                  <Box>
                    <Flex align="center" gap={2} mb={1} flexWrap="wrap">
                      <Text fontWeight={600}>{connection.display_name}</Text>
                      {connection.is_demo && (
                        <Badge
                          colorScheme="yellow"
                          variant="subtle"
                          fontSize="10px"
                          textTransform="uppercase"
                          letterSpacing="0.08em"
                        >
                          Demo
                        </Badge>
                      )}
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
                      {connection.connection_method_display} ·{" "}
                      {connection.platform_display}
                    </Kicker>
                    <Text fontSize="sm" color="ink.dim" mt={2}>
                      {formatSyncedAt(connection.last_synced_at)}
                    </Text>
                    {connection.last_error && (
                      <Text fontSize="sm" color="rust.500" mt={1}>
                        {connection.last_error}
                      </Text>
                    )}
                  </Box>

                  <Flex gap={2} flexWrap="wrap">
                    <Button
                      variant="fiscalOutline"
                      size="sm"
                      isLoading={syncingId === connection.id}
                      onClick={() => void handleSync(connection)}
                      isDisabled={!user?.email_verified}
                    >
                      Synchroniseren
                    </Button>
                    <Button
                      variant="fiscalOutline"
                      size="sm"
                      color="rust.500"
                      borderColor="line.DEFAULT"
                      _hover={{ borderColor: "rust.500", bg: "rust.50" }}
                      onClick={() => void handleDelete(connection)}
                    >
                      Verwijderen
                    </Button>
                  </Flex>
                </Flex>
              </FiscalCard>
            );
          })}
        </VStack>
      )}
    </VStack>
  );
}
