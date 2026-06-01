import { useEffect, useState } from "react";
import {
  Badge,
  Box,
  Button,
  Grid,
  Heading,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useLocation } from "react-router-dom";

import {
  downloadBox3ReportPdf,
  getBox3Summary,
  getTaxYearContext,
  type Box3Summary,
  type TaxYearContext,
} from "../api/tax";
import { createPeildatumSnapshot, getPeildatumSnapshot } from "../api/snapshots";
import AuthAlert from "../components/auth/AuthAlert";
import DisplayMoney from "../components/portfolio/DisplayMoney";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import ManualWealthSection from "../components/tax/ManualWealthSection";
import PremiumGate from "../components/common/PremiumGate";
import { useUser } from "../contexts/UserContext";
import { formatEur } from "../utils/formatMoney";
import { getApiErrorMessage, getApiErrorMessageAsync } from "../utils/apiError";
import { werkelijkReferenceLabel } from "../utils/referenceDate";
import { relevantTaxYear } from "../utils/taxYear";

const WERKELIJK_COMPONENT_LABELS: Record<string, string> = {
  dividend_eur: "Dividend",
  rente_bank_eur: "Rente banktegoeden",
  huur_eur: "Huurinkomsten",
  staking_eur: "Staking",
  overige_inkomsten_eur: "Overige inkomsten",
  reguliere_voordelen_eur: "Reguliere voordelen",
  waardemutatie_eur: "Waardemutatie",
  bijtelling_eur: "Bijtelling vastgoed",
  rente_schulden_eur: "Rente op schulden",
  woz_investering_eur: "WOZ-investeringen",
};

const WERKELIJK_SECTION_ID = "werkelijk-rendement";

const FORFAIT_STEP_LABELS: Record<string, string> = {
  schulden_aftrekbaar_eur: "Aftrekbare schulden",
  rendement_bank_eur: "Rendement banktegoeden",
  rendement_overig_eur: "Rendement overige bezittingen",
  rendement_schulden_eur: "Rendement schulden",
  belastbaar_rendement_eur: "Belastbaar rendement (R)",
  rendementsgrondslag_eur: "Rendementsgrondslag (RG)",
  grondslag_sparen_beleggen_eur: "Grondslag sparen en beleggen (GSB)",
  aandeel_percent: "Aandeel (%)",
  voordeel_eur: "Voordeel sparen en beleggen (V)",
  belasting_bruto_eur: "Belasting bruto",
  belasting_netto_eur: "Te betalen (forfaitair)",
  aftrek_dubbele_belasting_eur: "Aftrek dubbele belasting",
};

function StepTable({ steps }: { steps: Record<string, string> }) {
  return (
    <Box overflowX="auto">
      <Table size="sm" variant="simple">
        <Thead bg="backgroundCard">
          <Tr>
            <Th>Stap</Th>
            <Th isNumeric>Bedrag</Th>
          </Tr>
        </Thead>
        <Tbody>
          {Object.entries(steps).map(([key, value]) => (
            <Tr key={key}>
              <Td color="ink.dim">{FORFAIT_STEP_LABELS[key] ?? key}</Td>
              <Td isNumeric fontWeight={key.includes("belasting") ? 600 : 400}>
                {key.includes("percent") ? `${value}%` : formatEur(value)}
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
}

export default function TaxPositionPage() {
  const location = useLocation();
  const { user, permissions } = useUser();
  const [taxContext, setTaxContext] = useState<TaxYearContext | null>(null);
  const taxYear = taxContext?.relevant_tax_year ?? relevantTaxYear();
  const [summary, setSummary] = useState<Box3Summary | null>(null);
  const [hasSnapshot, setHasSnapshot] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [snapshotBusy, setSnapshotBusy] = useState(false);
  const [reportBusy, setReportBusy] = useState(false);
  const [reportMessage, setReportMessage] = useState("");

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    if (!location.pathname.includes("/werkelijk") || loading) {
      return;
    }
    const timer = window.setTimeout(() => {
      const target =
        document.getElementById(WERKELIJK_SECTION_ID) ??
        document.getElementById(`${WERKELIJK_SECTION_ID}-samenvatting`);
      target?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 150);
    return () => window.clearTimeout(timer);
  }, [location.pathname, loading, summary]);

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const ctx = await getTaxYearContext();
      setTaxContext(ctx);
      const year = ctx.relevant_tax_year;
      const snap = await getPeildatumSnapshot(year);
      setHasSnapshot(!!snap);
      const data = await getBox3Summary(year);
      setSummary(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Belastinggegevens laden mislukt."));
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateSnapshot() {
    setSnapshotBusy(true);
    try {
      await createPeildatumSnapshot(taxYear);
      await loadData();
    } catch (createError) {
      setError(getApiErrorMessage(createError, "Peildatum vastleggen mislukt."));
    } finally {
      setSnapshotBusy(false);
    }
  }

  function triggerDownload(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function handleDownloadPdf() {
    setReportBusy(true);
    setReportMessage("");
    try {
      const blob = await downloadBox3ReportPdf(taxYear);
      triggerDownload(blob, `box3-rapport-${taxYear}.pdf`);
      setReportMessage("Rapport gedownload (PDF).");
    } catch (reportError) {
      const msg =
        reportError instanceof Error
          ? reportError.message
          : await getApiErrorMessageAsync(reportError, "PDF laden mislukt.");
      setReportMessage(msg);
    } finally {
      setReportBusy(false);
    }
  }

  const forfait = summary?.forfaitair;
  const werkelijk = summary?.werkelijk;
  const comparison = summary?.comparison;

  return (
    <VStack align="stretch" spacing={8}>
      <Box>
        <Kicker mb={2}>Belasting · Box 3</Kicker>
        <Heading size="lg">Belastingpositie {taxYear}</Heading>
        <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7} maxW="2xl">
          Forfaitaire berekening en werkelijk rendement. De Belastingdienst past automatisch het
          laagste bedrag toe.
        </Text>
        {taxContext && (
          <Text color="taupe.500" fontSize="xs" mt={2} lineHeight={1.6}>
            {taxContext.rule}
            {user?.active_tax_year != null &&
              user.active_tax_year !== taxContext.relevant_tax_year && (
                <> · Profiel: belastingjaar {user.active_tax_year}</>
              )}
          </Text>
        )}
      </Box>

      {error && <AuthAlert tone="error">{error}</AuthAlert>}

      {loading ? (
        <Text color="ink.dim" fontSize="sm">
          Berekeningen laden…
        </Text>
      ) : (
        <>
          <Grid templateColumns={{ base: "1fr", lg: "repeat(3, 1fr)" }} gap={4}>
            <FiscalCard p={5}>
              <Kicker mb={2}>Te betalen (toegepast)</Kicker>
              {summary?.applied_tax_eur ? (
                <DisplayMoney amount={summary.applied_tax_eur} size="md" tone="accent" />
              ) : (
                <Text fontSize="2xl" color="ink.dim">
                  —
                </Text>
              )}
              {comparison && (
                <Text fontSize="sm" color="ink.dim" mt={3} lineHeight={1.6}>
                  {comparison.message}
                </Text>
              )}
            </FiscalCard>

            <FiscalCard p={5}>
              <Kicker mb={2}>Forfaitair</Kicker>
              {forfait?.available ? (
                <DisplayMoney amount={forfait.tax_due_eur ?? "0"} size="sm" />
              ) : (
                <Text color="ink.dim">—</Text>
              )}
              {forfait?.parameters_provisional && (
                <Badge variant="premium" mt={2}>
                  Voorlopige percentages
                </Badge>
              )}
            </FiscalCard>

            {permissions.isPremium ? (
              <FiscalCard p={5} id={`${WERKELIJK_SECTION_ID}-samenvatting`}>
                <Kicker mb={2}>Werkelijk rendement</Kicker>
                {werkelijk?.available ? (
                  <>
                    <DisplayMoney amount={werkelijk.tax_due_eur ?? "0"} size="sm" />
                    <Text fontSize="xs" color="taupe.500" mt={2} lineHeight={1.6}>
                      {werkelijk.is_provisional
                        ? werkelijkReferenceLabel()
                        : `Berekend over het volledige kalenderjaar ${taxYear}.`}
                    </Text>
                  </>
                ) : (
                  <Text color="ink.dim" fontSize="sm" lineHeight={1.6}>
                    {werkelijk?.message ?? "Geen berekening beschikbaar."}
                  </Text>
                )}
              </FiscalCard>
            ) : (
              <PremiumGate
                compact
                title="Werkelijk rendement"
                description="Vergelijk forfaitair met uw werkelijke rendement en zie welke methode voordeliger is."
              />
            )}
          </Grid>

          {!hasSnapshot && (
            <FiscalCard p={6}>
              <Text color="ink.dim" mb={4} lineHeight={1.7}>
                Leg eerst uw peildatum vast om Box 3 te berekenen.
              </Text>
              <Button variant="fiscal" size="sm" isLoading={snapshotBusy} onClick={() => void handleCreateSnapshot()}>
                Peildatum {taxYear} vastleggen
              </Button>
            </FiscalCard>
          )}

          {forfait?.available && forfait.calculation?.steps && (
            <FiscalCard p={5}>
              <Kicker mb={4}>Forfaitair · tussenstappen</Kicker>
              {forfait.box3_inputs && (
                <Grid
                  templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }}
                  gap={3}
                  mb={4}
                >
                  <Box>
                    <Text fontSize="xs" color="ink.dim">
                      Banktegoeden (B)
                    </Text>
                    <Text fontWeight={600}>{formatEur(forfait.box3_inputs.banktegoeden_eur)}</Text>
                  </Box>
                  <Box>
                    <Text fontSize="xs" color="ink.dim">
                      Overige bezittingen (O)
                    </Text>
                    <Text fontWeight={600}>
                      {formatEur(forfait.box3_inputs.overige_bezittingen_eur)}
                    </Text>
                  </Box>
                  <Box>
                    <Text fontSize="xs" color="ink.dim">
                      Schulden (S)
                    </Text>
                    <Text fontWeight={600}>{formatEur(forfait.box3_inputs.schulden_eur)}</Text>
                  </Box>
                </Grid>
              )}
              <StepTable steps={forfait.calculation.steps} />
              <Text fontSize="xs" color="taupe.500" mt={3}>
                {forfait.disclaimer}
              </Text>
            </FiscalCard>
          )}

          {permissions.isPremium && werkelijk?.available && werkelijk.calculation ? (
            <FiscalCard p={5} id={WERKELIJK_SECTION_ID} scrollMarginTop="24px">
              <Kicker mb={4}>Werkelijk rendement · onderdelen</Kicker>
              <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={3} mb={4}>
                <Box>
                  <Text fontSize="xs" color="ink.dim">
                    Startwaarde (1 jan)
                  </Text>
                  <Text fontWeight={600}>{formatEur(werkelijk.calculation.w_start_eur)}</Text>
                </Box>
                <Box>
                  <Text fontSize="xs" color="ink.dim">
                    Huidige waarde
                  </Text>
                  <Text fontWeight={600}>{formatEur(werkelijk.calculation.w_end_eur)}</Text>
                </Box>
                <Box>
                  <Text fontSize="xs" color="ink.dim">
                    Netto inleg
                  </Text>
                  <Text fontWeight={600}>{formatEur(werkelijk.calculation.netto_inleg_eur)}</Text>
                </Box>
                <Box>
                  <Text fontSize="xs" color="ink.dim">
                    Werkelijk rendement
                  </Text>
                  <Text fontWeight={600}>
                    {formatEur(werkelijk.calculation.werkelijk_rendement_eur)} (
                    {werkelijk.calculation.werkelijk_percent}%)
                  </Text>
                </Box>
              </Grid>
              <Box overflowX="auto">
                <Table size="sm">
                  <Tbody>
                    {Object.entries(werkelijk.calculation.components).map(([key, val]) => (
                      <Tr key={key}>
                        <Td color="ink.dim">{WERKELIJK_COMPONENT_LABELS[key] ?? key}</Td>
                        <Td isNumeric>{formatEur(val)}</Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
              <Text fontSize="xs" color="taupe.500" mt={3}>
                {werkelijk.disclaimer}
              </Text>
            </FiscalCard>
          ) : !permissions.isPremium ? (
            <Box id={WERKELIJK_SECTION_ID} scrollMarginTop="24px">
            <PremiumGate title="Werkelijk rendement · detail">
              <FiscalCard p={5}>
                <Kicker mb={2}>Werkelijk rendement · onderdelen</Kicker>
                <Text color="ink.dim" fontSize="sm">
                  Rendementscomponenten en vergelijking met forfaitair.
                </Text>
              </FiscalCard>
            </PremiumGate>
            </Box>
          ) : null}

          <ManualWealthSection taxYear={taxYear} onChanged={() => void loadData()} />

          {comparison && (
            <FiscalCard p={5}>
              <Kicker mb={3}>Vergelijking</Kicker>
              <Text
                color={comparison.werkelijk_is_beneficial ? "moss.500" : "ink.dim"}
                fontWeight={500}
              >
                {comparison.message}
              </Text>
              <Text fontSize="sm" color="ink.dim" mt={2}>
                Forfaitair: {formatEur(comparison.forfait_tax_eur)} · Werkelijk:{" "}
                {formatEur(comparison.werkelijk_tax_eur)} · Besparing:{" "}
                {formatEur(comparison.savings_eur)}
              </Text>
            </FiscalCard>
          )}

          <FiscalCard p={5}>
            <Kicker mb={3}>Box 3-rapport</Kicker>
            <Text color="ink.dim" fontSize="sm" mb={4} lineHeight={1.7}>
              Download onderbouwing: posities, handmatig vermogen en berekeningen als PDF.
            </Text>
            <Button
              variant="fiscal"
              size="sm"
              isLoading={reportBusy}
              onClick={() => void handleDownloadPdf()}
              isDisabled={!hasSnapshot}
            >
              Download PDF
            </Button>
            {reportMessage && (
              <Text fontSize="xs" color="taupe.500" mt={2}>
                {reportMessage}
              </Text>
            )}
          </FiscalCard>

          <Button as={RouterLink} to="/dashboard" variant="ghostNav" size="sm" maxW="fit-content">
            ← Terug naar dashboard
          </Button>
        </>
      )}
    </VStack>
  );
}
