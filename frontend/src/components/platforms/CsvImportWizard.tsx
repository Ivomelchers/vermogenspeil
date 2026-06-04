import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  Box,
  Button,
  Flex,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import {
  importPlatformCsv,
  previewPlatformCsv,
  type CsvImportResult,
  type CsvPreviewResult,
  type CsvPreviewTransaction,
} from "../../api/integrations";
import AuthAlert from "../auth/AuthAlert";
import { formatEur } from "../../utils/formatMoney";
import { getApiErrorMessage } from "../../utils/apiError";

const TYPE_LABELS: Record<string, string> = {
  buy: "Aankoop",
  sell: "Verkoop",
  dividend: "Dividend",
  fee: "Kosten",
  deposit: "Storting",
  withdrawal: "Opname",
  other: "Overig",
};

const STATUS_COLORS: Record<string, string> = {
  new: "moss",
  duplicate: "gray",
};

type FilterKey = "all" | "new" | "duplicate" | "issues";

interface CsvImportWizardProps {
  isOpen: boolean;
  file: File | null;
  platform?: string;
  onClose: () => void;
  onComplete: (result: CsvImportResult) => void;
}

function formatPreviewMessage(result: CsvImportResult): string {
  const base = result.trust_summary || `${result.transactions_imported} transacties geïmporteerd.`;
  if (!result.has_import_gaps) return base;
  const unknown = result.unknown_descriptions.slice(0, 3).join(", ");
  return `${base}${unknown ? ` Niet herkend: ${unknown}.` : ""}`;
}

export default function CsvImportWizard({
  isOpen,
  file,
  platform,
  onClose,
  onComplete,
}: CsvImportWizardProps) {
  const [step, setStep] = useState<"loading" | "preview" | "rejected" | "importing">("loading");
  const [preview, setPreview] = useState<CsvPreviewResult | null>(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<FilterKey>("new");

  const loadPreview = async () => {
    if (!file) return;
    setStep("loading");
    setError("");
    setPreview(null);
    try {
      const data = await previewPlatformCsv(file, { platform });
      setPreview(data);
      setStep(data.status === "rejected" ? "rejected" : "preview");
      setFilter(data.status === "ok" && data.summary && data.summary.new > 0 ? "new" : "all");
    } catch (err) {
      setError(getApiErrorMessage(err, "Preview mislukt."));
      setStep("rejected");
    }
  };

  useEffect(() => {
    if (isOpen && file) {
      void loadPreview();
      return;
    }
    if (!isOpen) {
      setPreview(null);
      setError("");
      setStep("loading");
    }
  }, [isOpen, file, platform]);

  const filteredTransactions = useMemo(() => {
    if (!preview?.transactions) return [];
    if (filter === "new") return preview.transactions.filter((t) => t.status === "new");
    if (filter === "duplicate") {
      return preview.transactions.filter((t) => t.status === "duplicate");
    }
    return preview.transactions;
  }, [preview, filter]);

  async function handleConfirm() {
    if (!file || !preview || preview.status !== "ok") return;
    setStep("importing");
    setError("");
    try {
      const result = await importPlatformCsv(file, {
        platform: preview.platform,
      });
      onComplete(result);
      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, "Import mislukt."));
      setStep("preview");
    }
  }

  function renderTransactionRow(tx: CsvPreviewTransaction) {
    return (
      <Tr key={tx.transaction_hash}>
        <Td fontSize="xs" whiteSpace="nowrap">
          {tx.date}
        </Td>
        <Td fontSize="xs">{TYPE_LABELS[tx.transaction_type] ?? tx.transaction_type}</Td>
        <Td fontSize="xs">
          <Text fontWeight={500}>{tx.symbol}</Text>
          <Text color="ink.faint" fontSize="10px" noOfLines={1}>
            {tx.name}
          </Text>
        </Td>
        <Td fontSize="xs" isNumeric>
          {tx.quantity}
        </Td>
        <Td fontSize="xs" isNumeric>
          {tx.total_eur ? formatEur(tx.total_eur) : "—"}
        </Td>
        <Td>
          <Badge
            colorScheme={STATUS_COLORS[tx.status] ?? "gray"}
            fontSize="9px"
            textTransform="uppercase"
          >
            {tx.status === "new" ? "Nieuw" : "Dubbel"}
          </Badge>
        </Td>
      </Tr>
    );
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader fontFamily="heading" fontWeight={500}>
          CSV controleren vóór import
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          {error && (
            <Box mb={4}>
              <AuthAlert tone="error">{error}</AuthAlert>
            </Box>
          )}

          {step === "loading" && (
            <Text fontSize="sm" color="ink.dim">
              Bestand analyseren…
            </Text>
          )}

          {step === "rejected" && preview?.status === "rejected" && (
            <VStack align="stretch" spacing={4}>
              <AuthAlert tone="info">{preview.message}</AuthAlert>
              <Box>
                <Text fontSize="xs" color="ink.faint" mb={1}>
                  Reden: {preview.failure_reason}
                </Text>
                {preview.file_headers.length > 0 && (
                  <Text fontSize="sm" color="ink.dim">
                    Kolommen in uw bestand: {preview.file_headers.join(", ")}
                  </Text>
                )}
              </Box>
              <Text fontSize="sm" color="ink.dim">
                Ondersteunde CSV-platformen:{" "}
                {preview.supported_platforms.map((p) => p.display_name).join(", ") || "geen"}
              </Text>
            </VStack>
          )}

          {step === "preview" && preview?.status === "ok" && preview.summary && (
            <VStack align="stretch" spacing={4}>
              <Flex gap={3} flexWrap="wrap">
                <Badge colorScheme="azure">{preview.platform_display}</Badge>
                <Text fontSize="sm" color="ink.dim">
                  {preview.summary.new} nieuw · {preview.summary.duplicate} al in portefeuille ·{" "}
                  {preview.summary.skipped_unrecognized + preview.summary.skipped_other} niet
                  verwerkt
                </Text>
              </Flex>

              {preview.column_mapping?.ai_used && (
                <Box
                  p={4}
                  border="1px solid"
                  borderColor="azure.200"
                  borderRadius="base"
                  bg="azure.50"
                >
                  <Text fontSize="sm" fontWeight={600} mb={2}>
                    Kolommen via AI gekoppeld (eenmalig)
                  </Text>
                  <Text fontSize="sm" color="ink.dim" mb={2}>
                    De vaste parser herkende deze export niet. We hebben alleen de kolomkoppen
                    laten koppelen; transacties worden nog steeds door onze eigen logica verwerkt.
                    Voeg onderstaande aliases toe in de code zodat volgende imports zonder AI
                    kunnen.
                  </Text>
                  {preview.column_mapping.maintenance_snippets.map((line) => (
                    <Text
                      key={line}
                      as="code"
                      display="block"
                      fontSize="xs"
                      whiteSpace="pre-wrap"
                      color="ink.faint"
                      mb={1}
                    >
                      {line}
                    </Text>
                  ))}
                </Box>
              )}

              {preview.has_schema_warnings && preview.column_schema && (
                <Box
                  p={4}
                  border="1px solid"
                  borderColor="ochre.200"
                  borderRadius="base"
                  bg="ochre.50"
                >
                  <Text fontSize="sm" fontWeight={600} mb={2}>
                    Kolomschema ({preview.column_schema.schema_version})
                  </Text>
                  {preview.column_schema.mapped_columns && (
                    <Text fontSize="xs" color="ink.dim" mb={2}>
                      Gekoppeld:{" "}
                      {Object.entries(preview.column_schema.mapped_columns)
                        .map(([k, v]) => `${k} ← ${v}`)
                        .join(" · ")}
                    </Text>
                  )}
                  {preview.column_schema.schema_warnings
                    .filter((w) => w.severity === "warning")
                    .map((w) => (
                      <Text key={`${w.code}-${w.file_header}`} fontSize="sm" color="ink.primary" mb={1}>
                        {w.message}
                      </Text>
                    ))}
                  {preview.column_schema.suggested_aliases.map((s) => (
                    <Text key={s.file_header} fontSize="xs" color="ink.faint">
                      Suggestie voor team: &quot;{s.file_header}&quot; ≈ {s.canonical_label} (
                      {Math.round(s.confidence * 100)}%)
                    </Text>
                  ))}
                </Box>
              )}

              {preview.has_import_gaps && (
                <AuthAlert tone="info">
                  Niet alle regels uit het bestand zijn herkend. Controleer de problemen hieronder
                  vóór u bevestigt.
                </AuthAlert>
              )}

              <Flex gap={2} flexWrap="wrap">
                {(
                  [
                    ["new", `Nieuw (${preview.summary.new})`],
                    ["duplicate", `Dubbel (${preview.summary.duplicate})`],
                    ["all", "Alles"],
                    ["issues", `Problemen (${preview.issues.length})`],
                  ] as const
                ).map(([key, label]) => (
                  <Button
                    key={key}
                    size="xs"
                    variant={filter === key ? "solid" : "outline"}
                    colorScheme={filter === key ? "blue" : "gray"}
                    onClick={() => setFilter(key)}
                  >
                    {label}
                  </Button>
                ))}
              </Flex>

              {filter === "issues" ? (
                <Box fontSize="sm">
                  {preview.issues.length === 0 ? (
                    <Text color="ink.dim">Geen problemen.</Text>
                  ) : (
                    preview.issues.map((issue) => (
                      <Box
                        key={`${issue.line_number}-${issue.reason}`}
                        py={2}
                        borderBottom="1px solid"
                        borderColor="line.soft"
                      >
                        <Text fontWeight={500}>
                          Regel {issue.line_number}: {issue.description || issue.reason}
                        </Text>
                        <Text color="ink.faint" fontSize="xs">
                          {issue.suggestion}
                        </Text>
                      </Box>
                    ))
                  )}
                </Box>
              ) : (
                <Box overflowX="auto" maxH="320px">
                  <Table size="sm" variant="simple">
                    <Thead position="sticky" top={0} bg="backgroundCard" zIndex={1}>
                      <Tr>
                        <Th>Datum</Th>
                        <Th>Type</Th>
                        <Th>Asset</Th>
                        <Th isNumeric>Aantal</Th>
                        <Th isNumeric>Totaal</Th>
                        <Th>Status</Th>
                      </Tr>
                    </Thead>
                    <Tbody>{filteredTransactions.map(renderTransactionRow)}</Tbody>
                  </Table>
                  {preview.summary.transactions_truncated && (
                    <Text fontSize="xs" color="ink.faint" mt={2}>
                      Eerste {preview.transactions.length} van{" "}
                      {preview.summary.transactions_total} transacties getoond.
                    </Text>
                  )}
                </Box>
              )}

              <Text fontSize="xs" color="ink.faint">
                {preview.confirm_hint}
              </Text>
            </VStack>
          )}
        </ModalBody>
        <ModalFooter gap={2}>
          <Button variant="ghost" onClick={onClose}>
            Annuleren
          </Button>
          {preview?.status === "ok" && (
            <Button
              variant="fiscal"
              isLoading={step === "importing"}
              isDisabled={!preview.can_confirm_import}
              onClick={() => void handleConfirm()}
            >
              {preview.summary?.new
                ? `Importeer ${preview.summary.new} transactie(s)`
                : "Niets nieuws te importeren"}
            </Button>
          )}
          {preview?.status === "rejected" && (
            <Button as={RouterLink} to="/platforms/add?method=csv" variant="fiscalOutline" onClick={onClose}>
              Ander platform
            </Button>
          )}
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

export { formatPreviewMessage };
