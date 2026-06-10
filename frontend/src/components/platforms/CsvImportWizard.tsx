import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  Box,
  Button,
  Divider,
  Flex,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  SimpleGrid,
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

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  new: { label: "Nieuw", color: "moss" },
  duplicate: { label: "Al in portefeuille", color: "taupe" },
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

function formatAssetLabel(tx: CsvPreviewTransaction): { title: string; subtitle: string | null } {
  const isCash = tx.symbol === "EUR" || (!tx.name && tx.symbol === "EUR");
  if (isCash) {
    return { title: "Cash (EUR)", subtitle: null };
  }
  if (tx.name && tx.name !== tx.symbol) {
    return { title: tx.name, subtitle: tx.symbol.length >= 10 ? tx.symbol : null };
  }
  return { title: tx.symbol || "Onbekend", subtitle: null };
}

function SummaryCard({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: number | string;
  hint?: string;
  accent?: string;
}) {
  return (
    <Box
      p={4}
      bg="paper"
      border="1px solid"
      borderColor="line.soft"
      borderRadius="base"
      boxShadow="sm"
      borderTopWidth="3px"
      borderTopColor={accent ?? "azure.500"}
    >
      <Text fontSize="xs" color="ink.faint" textTransform="uppercase" letterSpacing="0.06em" mb={1}>
        {label}
      </Text>
      <Text fontFamily="heading" fontSize="2xl" fontWeight={500} color="ink.primary" lineHeight={1.1}>
        {value}
      </Text>
      {hint && (
        <Text fontSize="xs" color="ink.dim" mt={1}>
          {hint}
        </Text>
      )}
    </Box>
  );
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
      setError(getApiErrorMessage(err, "We konden het bestand niet lezen."));
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

  const skippedCount = useMemo(() => {
    if (!preview?.summary) return 0;
    return preview.summary.skipped_unrecognized + preview.summary.skipped_other;
  }, [preview]);

  async function handleConfirm() {
    if (!file || !preview || preview.status !== "ok") return;
    setStep("importing");
    setError("");
    try {
      const result = await importPlatformCsv(file, {
        platform: preview.platform,
        columnMapping: preview.column_mapping?.mapped_columns,
      });
      onComplete(result);
      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, "Import mislukt."));
      setStep("preview");
    }
  }

  function renderTransactionRow(tx: CsvPreviewTransaction) {
    const asset = formatAssetLabel(tx);
    const status = STATUS_LABELS[tx.status] ?? { label: tx.status, color: "gray" };
    const timeShort = tx.time?.slice(0, 5) ?? "";

    return (
      <Tr key={tx.transaction_hash} _hover={{ bg: "azure.50" }}>
        <Td fontSize="xs" whiteSpace="nowrap" color="ink.dim">
          {tx.line_number ? (
            <Text as="span" color="ink.faint" mr={2}>
              #{tx.line_number}
            </Text>
          ) : null}
          {tx.date}
          {timeShort ? ` · ${timeShort}` : ""}
        </Td>
        <Td fontSize="xs" maxW="180px">
          <Text color="ink.primary" noOfLines={2} title={tx.description}>
            {tx.description?.trim() || "—"}
          </Text>
        </Td>
        <Td fontSize="xs">
          <Badge variant="subtle" colorScheme="azure" fontWeight={500} fontSize="10px">
            {TYPE_LABELS[tx.transaction_type] ?? tx.transaction_type}
          </Badge>
        </Td>
        <Td fontSize="xs" maxW="200px">
          <Text fontWeight={500} color="ink.primary" noOfLines={2}>
            {asset.title}
          </Text>
          {asset.subtitle && (
            <Text color="ink.faint" fontSize="10px" noOfLines={1}>
              {asset.subtitle}
            </Text>
          )}
        </Td>
        <Td fontSize="xs" color="ink.dim">
          {tx.currency && tx.currency !== "EUR" ? tx.currency : "EUR"}
        </Td>
        <Td fontSize="xs" isNumeric color="ink.dim">
          {tx.quantity ?? "—"}
        </Td>
        <Td fontSize="xs" isNumeric color="ink.dim">
          {tx.price_eur ? formatEur(tx.price_eur) : "—"}
        </Td>
        <Td fontSize="xs" isNumeric color="ink.dim">
          {tx.fee_eur && tx.fee_eur !== "0.00" ? formatEur(tx.fee_eur) : "—"}
        </Td>
        <Td fontSize="xs" isNumeric fontWeight={500}>
          {tx.total_eur ? formatEur(tx.total_eur) : "—"}
        </Td>
        <Td>
          <Badge colorScheme={status.color} fontSize="9px" variant="subtle">
            {status.label}
          </Badge>
        </Td>
      </Tr>
    );
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="6xl" scrollBehavior="inside">
      <ModalOverlay bg="blackAlpha.400" />
      <ModalContent maxW="960px" bg="background">
        <ModalHeader fontFamily="heading" fontWeight={500} pb={2}>
          Import controleren
          {file && (
            <Text fontSize="sm" fontWeight={400} color="ink.dim" mt={1}>
              {file.name}
            </Text>
          )}
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pt={2}>
          {error && (
            <Box mb={4}>
              <AuthAlert tone="error">{error}</AuthAlert>
            </Box>
          )}

          {step === "loading" && (
            <Box py={8} textAlign="center">
              <Text fontSize="sm" color="ink.dim">
                Uw export wordt gelezen…
              </Text>
            </Box>
          )}

          {step === "rejected" && preview?.status === "rejected" && (
            <VStack align="stretch" spacing={4}>
              <AuthAlert tone="info">
                {preview.message ??
                  "Dit bestand kunnen we niet importeren. Gebruik de officiële transactie-export van uw broker."}
              </AuthAlert>
              {preview.requested_platform === "degiro" && (
                <Text fontSize="sm" color="ink.dim">
                  Tip: download in DEGIRO het bestand <strong>Transactions</strong> (CSV) en upload dat
                  opnieuw.
                </Text>
              )}
              {preview.matches && preview.matches.length > 0 && (
                <Text fontSize="sm" color="ink.dim">
                  Dit bestand lijkt op{" "}
                  <strong>{preview.matches.map((m) => m.platform_display).join(", ")}</strong>. Kies
                  het juiste platform vóór upload.
                </Text>
              )}
            </VStack>
          )}

          {step === "preview" && preview?.status === "ok" && preview.summary && (
            <VStack align="stretch" spacing={5}>
              <Flex align="center" gap={2} flexWrap="wrap">
                <Badge colorScheme="azure" px={2} py={1} fontSize="xs">
                  {preview.platform_display}
                </Badge>
                <Text fontSize="sm" color="ink.dim">
                  {preview.summary.rows_in_file} regel(s) in bestand ·{" "}
                  {preview.summary.rows_recognized} herkend als transactie
                </Text>
              </Flex>

              <SimpleGrid columns={{ base: 2, md: 4 }} spacing={3}>
                <SummaryCard
                  label="Nieuw"
                  value={preview.summary.new}
                  hint="Worden toegevoegd"
                  accent="moss.500"
                />
                <SummaryCard
                  label="Al bekend"
                  value={preview.summary.duplicate}
                  hint="Staat al in portefeuille"
                  accent="taupe.500"
                />
                <SummaryCard
                  label="Overgeslagen"
                  value={skippedCount}
                  hint="Komen niet in import"
                  accent={skippedCount > 0 ? "rust.500" : "line.DEFAULT"}
                />
                <SummaryCard
                  label="Totaal herkend"
                  value={preview.summary.rows_recognized}
                  hint={`Van ${preview.summary.rows_in_file} regels`}
                  accent="azure.500"
                />
              </SimpleGrid>

              {preview.column_mapping?.ai_used && (
                <Box
                  px={4}
                  py={3}
                  borderRadius="base"
                  bg="azure.50"
                  border="1px solid"
                  borderColor="azure.200"
                >
                  <Text fontSize="sm" color="ink.primary">
                    Dit exportformaat zagen we nog niet. We hebben de kolommen automatisch gekoppeld
                    — controleer of bedragen en datums kloppen.
                  </Text>
                </Box>
              )}

              {(preview.column_mapping?.learned_user || preview.column_mapping?.learned_shared) &&
                !preview.column_mapping?.ai_used && (
                  <Box px={4} py={3} borderRadius="base" bg="moss.50" border="1px solid" borderColor="moss.50">
                    <Text fontSize="sm" color="ink.primary">
                      We herkennen dit type export van een eerdere import.
                    </Text>
                  </Box>
                )}

              {preview.has_instrument_gaps && preview.instrument_preview && (
                <Box
                  px={4}
                  py={3}
                  borderRadius="base"
                  bg="gold.50"
                  border="1px solid"
                  borderColor="line.soft"
                >
                  <Text fontSize="sm" fontWeight={500} color="ink.primary" mb={1}>
                    Koers mogelijk later beschikbaar
                  </Text>
                  <Text fontSize="sm" color="ink.dim">
                    Voor {preview.instrument_preview.unmapped_count} belegging(en) zoeken we na
                    import automatisch een koers op. Uw transacties worden wel opgeslagen.
                  </Text>
                </Box>
              )}

              {(preview.has_row_gaps ?? preview.has_import_gaps) && skippedCount > 0 && (
                <AuthAlert tone="info">
                  {skippedCount === 1
                    ? "1 regel uit uw bestand nemen we niet mee. Bekijk het tabblad Problemen."
                    : `${skippedCount} regels uit uw bestand nemen we niet mee. Bekijk het tabblad Problemen.`}
                </AuthAlert>
              )}

              <Divider borderColor="line.soft" />

              <Flex gap={2} flexWrap="wrap">
                {(
                  [
                    ["new", `Nieuw (${preview.summary.new})`],
                    ["duplicate", `Al bekend (${preview.summary.duplicate})`],
                    ["all", `Alles (${preview.transactions.length})`],
                    ["issues", `Problemen (${preview.issues.length})`],
                  ] as const
                ).map(([key, label]) => (
                  <Button
                    key={key}
                    size="sm"
                    variant={filter === key ? "solid" : "ghost"}
                    colorScheme={filter === key ? "blue" : "gray"}
                    onClick={() => setFilter(key)}
                  >
                    {label}
                  </Button>
                ))}
              </Flex>

              {filter === "issues" ? (
                <VStack align="stretch" spacing={0} divider={<Divider borderColor="line.soft" />}>
                  {preview.issues.length === 0 ? (
                    <Text fontSize="sm" color="ink.dim" py={4}>
                      Geen overgeslagen regels — alles uit dit bestand is verwerkt.
                    </Text>
                  ) : (
                    preview.issues.map((issue) => (
                      <Box key={`${issue.line_number}-${issue.reason}`} py={4}>
                        <Flex gap={2} align="center" mb={1} flexWrap="wrap">
                          <Badge colorScheme="rust" fontSize="10px">
                            Regel {issue.line_number}
                          </Badge>
                          <Badge variant="outline" colorScheme="gray" fontSize="10px">
                            {issue.reason_label ?? issue.reason}
                          </Badge>
                        </Flex>
                        {issue.description && (
                          <Text fontWeight={500} fontSize="sm" color="ink.primary" mb={1}>
                            {issue.description}
                          </Text>
                        )}
                        <Text color="ink.dim" fontSize="sm">
                          {issue.suggestion}
                        </Text>
                      </Box>
                    ))
                  )}
                </VStack>
              ) : (
                <Box
                  overflowX="auto"
                  border="1px solid"
                  borderColor="line.soft"
                  borderRadius="base"
                  bg="paper"
                >
                  <Table size="sm" variant="simple">
                    <Thead>
                      <Tr bg="backgroundCard">
                        <Th fontSize="10px" textTransform="uppercase" letterSpacing="0.05em">
                          Datum
                        </Th>
                        <Th fontSize="10px" textTransform="uppercase" letterSpacing="0.05em">
                          Omschrijving
                        </Th>
                        <Th fontSize="10px" textTransform="uppercase" letterSpacing="0.05em">
                          Type
                        </Th>
                        <Th fontSize="10px" textTransform="uppercase" letterSpacing="0.05em">
                          Belegging
                        </Th>
                        <Th fontSize="10px" textTransform="uppercase" letterSpacing="0.05em">
                          Valuta
                        </Th>
                        <Th
                          fontSize="10px"
                          textTransform="uppercase"
                          letterSpacing="0.05em"
                          isNumeric
                        >
                          Aantal
                        </Th>
                        <Th
                          fontSize="10px"
                          textTransform="uppercase"
                          letterSpacing="0.05em"
                          isNumeric
                        >
                          Koers
                        </Th>
                        <Th
                          fontSize="10px"
                          textTransform="uppercase"
                          letterSpacing="0.05em"
                          isNumeric
                        >
                          Kosten
                        </Th>
                        <Th
                          fontSize="10px"
                          textTransform="uppercase"
                          letterSpacing="0.05em"
                          isNumeric
                        >
                          Totaal
                        </Th>
                        <Th fontSize="10px" textTransform="uppercase" letterSpacing="0.05em">
                          Status
                        </Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {filteredTransactions.length === 0 ? (
                        <Tr>
                          <Td colSpan={10} py={8} textAlign="center" color="ink.dim" fontSize="sm">
                            Geen transacties in deze weergave.
                          </Td>
                        </Tr>
                      ) : (
                        filteredTransactions.map(renderTransactionRow)
                      )}
                    </Tbody>
                  </Table>
                  {preview.summary.transactions_truncated && (
                    <Text fontSize="xs" color="ink.faint" p={3} borderTop="1px solid" borderColor="line.soft">
                      Eerste {preview.transactions.length} van {preview.summary.transactions_total}{" "}
                      transacties getoond.
                    </Text>
                  )}
                </Box>
              )}

              {preview.confirm_hint && (
                <Text fontSize="sm" color="ink.dim" lineHeight="tall">
                  {preview.confirm_hint}
                </Text>
              )}
            </VStack>
          )}
        </ModalBody>
        <ModalFooter gap={2} borderTop="1px solid" borderColor="line.soft" bg="paper">
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
                ? `${preview.summary.new} transactie${preview.summary.new === 1 ? "" : "s"} importeren`
                : "Niets nieuws te importeren"}
            </Button>
          )}
          {preview?.status === "rejected" && (
            <Button
              as={RouterLink}
              to="/platforms/add?method=csv"
              variant="fiscalOutline"
              onClick={onClose}
            >
              Opnieuw proberen
            </Button>
          )}
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

export { formatPreviewMessage };
