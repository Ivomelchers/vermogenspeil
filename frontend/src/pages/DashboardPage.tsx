import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Flex,
  Grid,
  HStack,
  Link,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import { getDashboardSummary, type DashboardSummary } from "../api/portfolio";
import {
  createPeildatumSnapshot,
  getPeildatumSnapshot,
  type PeildatumSnapshot,
} from "../api/snapshots";
import {
  getForfaitairBox3,
  getTaxYearContext,
  type ForfaitairBox3Summary,
} from "../api/tax";
import { relevantTaxYear } from "../utils/taxYear";
import AllocationChart from "../components/dashboard/AllocationChart";
import DashboardHero from "../components/dashboard/DashboardHero";
import DashboardPositionsTable from "../components/dashboard/DashboardPositionsTable";
import InsightGrid from "../components/dashboard/InsightGrid";
import PlatformStrip from "../components/dashboard/PlatformStrip";
import PortfolioTrendChart from "../components/dashboard/PortfolioTrendChart";
import RecentActivityFeed from "../components/dashboard/RecentActivityFeed";
import WinnersLosersPanel from "../components/dashboard/WinnersLosersPanel";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import SectionHeader from "../components/common/SectionHeader";
import { useUser } from "../contexts/UserContext";
import { formatEur } from "../utils/formatMoney";
import { getApiErrorMessage } from "../utils/apiError";

export default function DashboardPage() {
  const { user } = useUser();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [peildatum, setPeildatum] = useState<PeildatumSnapshot | null>(null);
  const [forfaitair, setForfaitair] = useState<ForfaitairBox3Summary | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [snapshotBusy, setSnapshotBusy] = useState(false);
  const [error, setError] = useState("");
  const [snapshotMessage, setSnapshotMessage] = useState("");

  const [taxYear, setTaxYear] = useState(relevantTaxYear());

  useEffect(() => {
    void loadSummary();
  }, []);

  async function loadSummary() {
    setLoading(true);
    setError("");
    setSnapshotMessage("");
    try {
      const ctx = await getTaxYearContext();
      const year = ctx.relevant_tax_year;
      setTaxYear(year);
      const data = await getDashboardSummary();
      setSummary(data);
      const snap = await getPeildatumSnapshot(year);
      setPeildatum(snap);
      if (snap) {
        const tax = await getForfaitairBox3(year);
        setForfaitair(tax);
      } else {
        setForfaitair(null);
      }
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Dashboard laden mislukt."));
    } finally {
      setLoading(false);
    }
  }

  async function handleCreatePeildatum() {
    setSnapshotBusy(true);
    setSnapshotMessage("");
    try {
      const snap = await createPeildatumSnapshot(taxYear);
      setPeildatum(snap);
      const tax = await getForfaitairBox3(taxYear);
      setForfaitair(tax);
      setSnapshotMessage(`Peildatum ${taxYear} vastgelegd.`);
    } catch (createError) {
      setSnapshotMessage(
        getApiErrorMessage(createError, "Peildatum vastleggen mislukt."),
      );
    } finally {
      setSnapshotBusy(false);
    }
  }

  const greetingName = user?.first_name || user?.email.split("@")[0] || "daar";
  const hasPositions = (summary?.positions_count ?? 0) > 0;

  return (
    <Box mx={{ base: -6, md: -12 }} mt={{ base: -5, md: -6 }}>
      <VStack align="stretch" spacing={0}>
        {error && (
          <Box px={{ base: 6, md: 12 }} pt={4}>
            <AuthAlert tone="error">{error}</AuthAlert>
          </Box>
        )}

        <Box px={{ base: 6, md: 12 }}>
          <DashboardHero
            greetingName={greetingName}
            summary={summary}
            loading={loading}
            taxYear={taxYear}
            forfaitair={forfaitair}
            peildatum={peildatum}
            hasPositions={hasPositions}
            snapshotBusy={snapshotBusy}
            onCreatePeildatum={() => void handleCreatePeildatum()}
            snapshotMessage={snapshotMessage}
          />
        </Box>

        {!loading && !hasPositions && (
          <Box px={{ base: 6, md: 12 }} py={8}>
            <FiscalCard elevated p={8} textAlign="center">
              <Text
                fontFamily="heading"
                fontStyle="italic"
                fontSize="lg"
                color="ink.dim"
                mb={4}
              >
                Nog geen posities — koppel een broker of voeg handmatig assets
                toe.
              </Text>
              <HStack spacing={3} justify="center" flexWrap="wrap">
                <Button as={RouterLink} to="/platforms" variant="fiscal">
                  Platform koppelen
                </Button>
                <Button
                  as={RouterLink}
                  to="/portfolio/manual/asset"
                  variant="fiscalOutline"
                >
                  Asset toevoegen
                </Button>
              </HStack>
            </FiscalCard>
          </Box>
        )}

        {hasPositions && summary && (
          <VStack align="stretch" spacing={10} px={{ base: 6, md: 12 }} py={8}>
            <Box>
              <SectionHeader
                title={
                  <>
                    Portefeuille <Text as="em">inzichten</Text>
                  </>
                }
                kicker="all-time · alle platformen"
              />
              <InsightGrid summary={summary} />
            </Box>

            <Box>
              <SectionHeader
                title={
                  <>
                    Vermogensontwikkeling <Text as="em">over tijd</Text>
                  </>
                }
                kicker="waarde versus cost basis · 12 maanden"
              />
              <FiscalCard elevated p={{ base: 4, md: 6 }}>
                <PortfolioTrendChart
                  points={summary.value_history ?? []}
                  valuationNote={summary.valuation_note}
                />
              </FiscalCard>
            </Box>

            {summary.movers && Object.keys(summary.movers).length > 0 && (
              <Box>
                <SectionHeader
                  title={
                    <>
                      Winnaars & <Text as="em">verliezers</Text>
                    </>
                  }
                  kicker="kies periode"
                />
                <WinnersLosersPanel movers={summary.movers} />
              </Box>
            )}

            <Grid templateColumns={{ base: "1fr", lg: "1fr 1fr" }} gap={8}>
              <Box>
                <SectionHeader
                  title={
                    <>
                      Platformen <Text as="em">& koppelingen</Text>
                    </>
                  }
                  kicker={`${summary.platforms.length} actief`}
                  action={
                    <Link
                      as={RouterLink}
                      to="/platforms"
                      fontSize="xs"
                      color="azure.500"
                    >
                      Beheer →
                    </Link>
                  }
                />
                <PlatformStrip platforms={summary.platforms} />
              </Box>

              {summary.by_category.length > 0 && (
                <Box>
                  <SectionHeader
                    title="Vermogensverdeling"
                    kicker="box 3 — categorieën"
                  />
                  <FiscalCard elevated p={5}>
                    <AllocationChart
                      categories={summary.by_category}
                      totalLabel={formatEur(summary.total_value_eur)}
                    />
                  </FiscalCard>
                </Box>
              )}
            </Grid>

            <Grid templateColumns={{ base: "1fr", xl: "1fr 1fr" }} gap={8}>
              <Box>
                <Flex justify="space-between" align="center" mb={3}>
                  <SectionHeader
                    title={
                      <>
                        Posities <Text as="em">top</Text>
                      </>
                    }
                    kicker={`${summary.positions_count} posities`}
                    mb={0}
                  />
                  <Link
                    as={RouterLink}
                    to="/portfolio"
                    fontSize="xs"
                    color="azure.500"
                  >
                    Alles →
                  </Link>
                </Flex>
                <DashboardPositionsTable
                  positions={summary.positions}
                  totalCount={summary.positions_count}
                />
              </Box>

              <Box>
                <Flex justify="space-between" align="center" mb={3}>
                  <Kicker>Recente activiteit</Kicker>
                  <Link
                    as={RouterLink}
                    to="/transactions"
                    fontSize="xs"
                    color="azure.500"
                  >
                    Alle transacties →
                  </Link>
                </Flex>
                <FiscalCard elevated p={0} overflow="hidden">
                  <RecentActivityFeed items={summary.recent_activity ?? []} />
                </FiscalCard>
              </Box>
            </Grid>

            <Text
              fontSize="xs"
              color="ink.faint"
              textAlign="center"
              fontFamily="heading"
              fontStyle="italic"
              pt={4}
            >
              Fiscaal inzicht — geen fiscaal advies · MijnVermogen ©{" "}
              {new Date().getFullYear()}
            </Text>
          </VStack>
        )}
      </VStack>
    </Box>
  );
}
