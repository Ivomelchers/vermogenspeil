import { useEffect, useState } from "react";
import {
  Badge,
  Box,
  Button,
  Grid,
  SimpleGrid,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import { getBox3Summary, getTaxYearContext, type Box3Summary, type TaxYearContext } from "../api/tax";
import AuthAlert from "../components/auth/AuthAlert";
import DisplayMoney from "../components/portfolio/DisplayMoney";
import FiscalCard from "../components/common/FiscalCard";
import FiscalDisclaimer from "../components/common/FiscalDisclaimer";
import FiscalNote from "../components/common/FiscalNote";
import Kicker from "../components/common/Kicker";
import PremiumGate from "../components/common/PremiumGate";
import SectionHeader from "../components/common/SectionHeader";
import StatStrip from "../components/common/StatStrip";
import MotionSection from "../components/layout/MotionSection";
import PageHeader from "../components/layout/PageHeader";
import PageShell from "../components/layout/PageShell";
import { useUser } from "../contexts/UserContext";
import { formatEur } from "../utils/formatMoney";
import { getApiErrorMessage } from "../utils/apiError";
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

export default function WerkelijkRendementPage() {
  const { permissions } = useUser();
  const [taxContext, setTaxContext] = useState<TaxYearContext | null>(null);
  const taxYear = taxContext?.relevant_tax_year ?? relevantTaxYear();
  const [summary, setSummary] = useState<Box3Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError("");
    try {
      const ctx = await getTaxYearContext();
      setTaxContext(ctx);
      const data = await getBox3Summary(ctx.relevant_tax_year);
      setSummary(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Belastinggegevens laden mislukt."));
    } finally {
      setLoading(false);
    }
  }

  const forfait = summary?.forfaitair;
  const werkelijk = summary?.werkelijk;
  const comparison = summary?.comparison;

  return (
    <PageShell>
      <MotionSection>
        <PageHeader
          kicker={`Werkelijk rendement · ${taxYear}`}
          title={
            <>
              Werkelijk <Text as="em">rendement</Text>
            </>
          }
          subtitle="De Belastingdienst rekent standaard met een forfaitair (fictief) rendement. Als uw werkelijke rendement lager uitkomt, mag u dat aantonen en betaalt u mogelijk minder belasting."
        />
      </MotionSection>

      <MotionSection>
        <FiscalDisclaimer>
          <strong>Let op:</strong> de definitieve keuze tussen forfait en werkelijk rendement maakt u pas bij de
          aangifte, nadat het boekjaar is afgelopen. MijnVermogen biedt geen fiscaal advies.
        </FiscalDisclaimer>
      </MotionSection>

      <MotionSection>
        <FiscalNote>
          <strong>Wat is werkelijk rendement?</strong> De Belastingdienst berekent Box 3 standaard met forfaitaire
          percentages per categorie. Als uw werkelijke rendement lager is, kan opgeven bij de aangifte voordelig
          zijn — op 31 december staat het definitieve beeld vast.
        </FiscalNote>
      </MotionSection>

      {error && (
        <MotionSection>
          <AuthAlert tone="error">{error}</AuthAlert>
        </MotionSection>
      )}

      {loading ? (
        <MotionSection>
          <Text color="ink.dim" fontStyle="italic">
            Berekeningen laden…
          </Text>
        </MotionSection>
      ) : !permissions.isPremium ? (
        <MotionSection>
          <PremiumGate
            title="Werkelijk rendement"
            description="Vergelijk forfaitair met uw werkelijke rendement, zie onderdelen per categorie en ontvang een signaal wanneer werkelijk voordeliger is."
          />
        </MotionSection>
      ) : (
        <>
          {comparison && forfait?.available && (
            <MotionSection>
              <StatStrip
                items={[
                  {
                    label: "Forfaitaire heffing",
                    value: formatEur(comparison.forfait_tax_eur),
                    sub: "36% over fictief rendement",
                  },
                  {
                    label: "Werkelijke heffing",
                    value: formatEur(comparison.werkelijk_tax_eur),
                    sub: "36% over werkelijk rendement",
                    tone: "moss",
                  },
                  {
                    label: "Aanbeveling",
                    value: comparison.werkelijk_is_beneficial ? "Werkelijk" : "Forfaitair",
                    sub: `besparing ${formatEur(comparison.savings_eur)}`,
                    tone: "ochre",
                  },
                ]}
                columns={3}
              />
            </MotionSection>
          )}

          <MotionSection>
            <SectionHeader
              title={
                <>
                  Samenvatting <Text as="em">werkelijk</Text>
                </>
              }
              kicker="premium · vergelijking met forfait"
            />
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              <FiscalCard elevated p={5}>
                <Kicker mb={2}>Forfaitair</Kicker>
                {forfait?.available ? (
                  <DisplayMoney amount={forfait.tax_due_eur ?? "0"} size="sm" />
                ) : (
                  <Text color="ink.dim">—</Text>
                )}
              </FiscalCard>
              <FiscalCard elevated p={5}>
                <Kicker mb={2}>Werkelijk rendement</Kicker>
                {werkelijk?.available ? (
                  <>
                    <DisplayMoney amount={werkelijk.tax_due_eur ?? "0"} size="sm" />
                    <Text fontSize="xs" color="taupe.500" mt={2}>
                      {werkelijk.is_provisional
                        ? werkelijkReferenceLabel()
                        : `Berekend over kalenderjaar ${taxYear}.`}
                    </Text>
                  </>
                ) : (
                  <Text color="ink.dim" fontSize="sm">
                    {werkelijk?.message ?? "Geen berekening beschikbaar."}
                  </Text>
                )}
              </FiscalCard>
            </SimpleGrid>
          </MotionSection>

          {werkelijk?.available && werkelijk.calculation && (
            <MotionSection>
              <SectionHeader
                title={
                  <>
                    Onderdelen <Text as="em">werkelijk rendement</Text>
                  </>
                }
                kicker="direct + indirect rendement"
              />
              <FiscalCard elevated p={5}>
                <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={4} mb={5}>
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
                    <Text fontWeight={600} color="moss.500">
                      {formatEur(werkelijk.calculation.werkelijk_rendement_eur)} (
                      {werkelijk.calculation.werkelijk_percent}%)
                    </Text>
                  </Box>
                </Grid>
                <Box overflowX="auto">
                  <Table size="sm">
                    <Thead>
                      <Tr>
                        <Th>Component</Th>
                        <Th isNumeric>Bedrag</Th>
                      </Tr>
                    </Thead>
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
                <FiscalNote mt={4} fontSize="xs">
                  {werkelijk.disclaimer}
                </FiscalNote>
              </FiscalCard>
            </MotionSection>
          )}

          {comparison && (
            <MotionSection>
              <FiscalCard elevated p={5}>
                <Kicker mb={3}>Vergelijking forfait vs. werkelijk</Kicker>
                <Text
                  color={comparison.werkelijk_is_beneficial ? "moss.500" : "ink.dim"}
                  fontWeight={500}
                  lineHeight={1.6}
                >
                  {comparison.message}
                </Text>
                {forfait?.parameters_provisional && (
                  <Badge variant="premium" mt={3}>
                    Voorlopige forfaitaire percentages
                  </Badge>
                )}
              </FiscalCard>
            </MotionSection>
          )}
        </>
      )}

      <MotionSection>
        <Button as={RouterLink} to="/belasting" variant="ghostNav" size="sm">
          ← Terug naar belastingpositie
        </Button>
      </MotionSection>
    </PageShell>
  );
}
