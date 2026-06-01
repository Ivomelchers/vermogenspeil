import { useEffect, useState } from "react";
import {
  Badge,
  Box,
  Button,
  Grid,
  SimpleGrid,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

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
import FiscalNote from "../components/common/FiscalNote";
import FiscalTable from "../components/common/FiscalTable";
import Kicker from "../components/common/Kicker";
import SectionHeader from "../components/common/SectionHeader";
import MotionSection from "../components/layout/MotionSection";
import PageHeader from "../components/layout/PageHeader";
import PageShell from "../components/layout/PageShell";
import { useUser } from "../contexts/UserContext";
import { formatEur } from "../utils/formatMoney";
import { getApiErrorMessage, getApiErrorMessageAsync } from "../utils/apiError";
import { relevantTaxYear } from "../utils/taxYear";

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
    <FiscalTable>
      <Thead>
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
    </FiscalTable>
  );
}

export default function TaxPositionPage() {
  const { user } = useUser();
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
  const comparison = summary?.comparison;

  return (
    <PageShell>
      <MotionSection>
        <PageHeader
          kicker="Belasting · Box 3"
          title={
            <>
              Belastingpositie <Text as="em">{taxYear}</Text>
            </>
          }
          subtitle="Forfaitaire Box 3-berekening op basis van uw peildatum. Werkelijk rendement en overig vermogen staan op aparte pagina's."
          meta={
            taxContext
              ? `${taxContext.rule}${
                  user?.active_tax_year != null &&
                  user.active_tax_year !== taxContext.relevant_tax_year
                    ? ` · Profiel: belastingjaar ${user.active_tax_year}`
                    : ""
                }`
              : undefined
          }
        />
      </MotionSection>

      {error && (
        <MotionSection>
          <AuthAlert tone="error">{error}</AuthAlert>
        </MotionSection>
      )}

      {loading ? (
        <MotionSection>
          <Text color="ink.dim" fontSize="sm" fontStyle="italic">
            Berekeningen laden…
          </Text>
        </MotionSection>
      ) : (
        <>
          <MotionSection>
            <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
              <FiscalCard elevated p={5}>
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

              <FiscalCard elevated p={5}>
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
            </SimpleGrid>
          </MotionSection>

          <MotionSection>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              <Box
                as={RouterLink}
                to="/belasting/werkelijk"
                display="block"
                _hover={{ textDecoration: "none" }}
              >
                <FiscalCard elevated p={5} _hover={{ borderColor: "azure.400" }}>
                  <Kicker mb={2}>Werkelijk rendement</Kicker>
                  <Text fontSize="sm" color="ink.dim" lineHeight={1.65} mb={3}>
                    Vergelijk forfaitair met uw werkelijke rendement en zie of opgeven voordelig kan zijn.
                  </Text>
                  <Text fontSize="sm" color="azure.500" fontWeight={500}>
                    Naar werkelijk rendement →
                  </Text>
                </FiscalCard>
              </Box>
              <Box
                as={RouterLink}
                to="/belasting/overig-vermogen"
                display="block"
                _hover={{ textDecoration: "none" }}
              >
                <FiscalCard elevated p={5} _hover={{ borderColor: "azure.400" }}>
                  <Kicker mb={2}>Overig vermogen</Kicker>
                  <Text fontSize="sm" color="ink.dim" lineHeight={1.65} mb={3}>
                    Banktegoeden, schulden en onroerend goed die niet via brokers binnenkomen.
                  </Text>
                  <Text fontSize="sm" color="azure.500" fontWeight={500}>
                    Naar overig vermogen →
                  </Text>
                </FiscalCard>
              </Box>
            </SimpleGrid>
          </MotionSection>

          {!hasSnapshot && (
            <MotionSection>
            <FiscalCard elevated p={6}>
              <Text color="ink.dim" mb={4} lineHeight={1.7}>
                Leg eerst uw peildatum vast om Box 3 te berekenen.
              </Text>
              <Button variant="fiscal" size="sm" isLoading={snapshotBusy} onClick={() => void handleCreateSnapshot()}>
                Peildatum {taxYear} vastleggen
              </Button>
            </FiscalCard>
            </MotionSection>
          )}

          {forfait?.available && forfait.calculation?.steps && (
            <MotionSection>
            <SectionHeader
              title={
                <>
                  Forfaitair · <Text as="em">tussenstappen</Text>
                </>
              }
              kicker="box 3 berekening"
            />
            <FiscalCard elevated p={5}>
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
              <FiscalNote mt={4} fontSize="xs">
                {forfait.disclaimer}
              </FiscalNote>
            </FiscalCard>
            </MotionSection>
          )}

          <MotionSection>
          <SectionHeader title="Box 3-rapport" kicker="pdf export" />
          <FiscalCard elevated p={5}>
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
          </MotionSection>

          <MotionSection>
          <Button as={RouterLink} to="/dashboard" variant="ghostNav" size="sm" maxW="fit-content">
            ← Terug naar dashboard
          </Button>
          </MotionSection>
        </>
      )}
    </PageShell>
  );
}
