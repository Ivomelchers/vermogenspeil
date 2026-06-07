import { useCallback, useEffect, useState } from "react";
import {
  Box,
  Button,
  Flex,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import {
  listImportBatches,
  purgeImportBatch,
  type PlatformImportBatch,
  type PlatformConnection,
} from "../../api/integrations";
import { formatDateNl } from "../../utils/formatMoney";
import { getApiErrorMessage } from "../../utils/apiError";

interface ImportHistoryPanelProps {
  connection: PlatformConnection;
  onChanged?: () => void;
}

export default function ImportHistoryPanel({
  connection,
  onChanged,
}: ImportHistoryPanelProps) {
  const [batches, setBatches] = useState<PlatformImportBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [purgingId, setPurgingId] = useState<number | null>(null);

  const loadBatches = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await listImportBatches(connection.id);
      setBatches(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Importgeschiedenis laden mislukt."));
    } finally {
      setLoading(false);
    }
  }, [connection.id]);

  useEffect(() => {
    void loadBatches();
  }, [loadBatches]);

  async function handlePurgeBatch(batch: PlatformImportBatch) {
    const label = batch.display_label || `Import #${batch.id}`;
    if (
      !window.confirm(
        `Weet u zeker dat u "${label}" wilt verwijderen? Alle ${batch.transactions_imported} transactie(s) uit deze import worden gewist.`,
      )
    ) {
      return;
    }
    setPurgingId(batch.id);
    setError("");
    try {
      await purgeImportBatch(batch.id);
      await loadBatches();
      onChanged?.();
    } catch (purgeError) {
      setError(getApiErrorMessage(purgeError, "Import verwijderen mislukt."));
    } finally {
      setPurgingId(null);
    }
  }

  if (loading) {
    return (
      <Text fontSize="sm" color="ink.dim" fontStyle="italic">
        Importgeschiedenis laden…
      </Text>
    );
  }

  if (batches.length === 0) {
    return (
      <Text fontSize="sm" color="ink.dim">
        Nog geen imports geregistreerd voor deze koppeling.
      </Text>
    );
  }

  return (
    <VStack align="stretch" spacing={2} mt={3}>
      <Text fontSize="xs" fontWeight={600} color="ink.dim" textTransform="uppercase" letterSpacing="0.06em">
        Importgeschiedenis
      </Text>
      {error && (
        <Text fontSize="sm" color="rust.500">
          {error}
        </Text>
      )}
      {batches.map((batch) => (
        <Flex
          key={batch.id}
          gap={3}
          p={3}
          bg="backgroundHover"
          borderRadius="base"
          border="1px solid"
          borderColor="line.soft"
          align={{ base: "stretch", md: "center" }}
          direction={{ base: "column", md: "row" }}
        >
          <Box flex={1} minW={0}>
            <Text fontSize="sm" fontWeight={500} noOfLines={1}>
              {batch.display_label}
            </Text>
            <Text fontSize="xs" color="ink.dim" mt={1}>
              {formatDateNl(batch.created_at)} · {batch.transactions_imported} nieuw
              {batch.transactions_skipped > 0
                ? ` · ${batch.transactions_skipped} dubbel`
                : ""}
              {batch.ai_used ? " · AI-kolommapping" : ""}
            </Text>
          </Box>
          <Flex gap={2} flexWrap="wrap">
            <Button
              as={RouterLink}
              to={`/transactions?import_batch_id=${batch.id}`}
              variant="ghostNav"
              size="xs"
              fontWeight={500}
            >
              Transacties
            </Button>
            <Button
              variant="fiscalOutline"
              size="xs"
              color="rust.500"
              isLoading={purgingId === batch.id}
              onClick={() => void handlePurgeBatch(batch)}
            >
              Import ongedaan maken
            </Button>
          </Flex>
        </Flex>
      ))}
    </VStack>
  );
}
