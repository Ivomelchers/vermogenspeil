import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Flex,
  Grid,
  HStack,
  Link,
  SimpleGrid,
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
import { getForfaitairBox3, getTaxYearContext, type ForfaitairBox3Summary } from "../api/tax";
import { relevantTaxYear } from "../utils/taxYear";
import AllocationChart from "../components/dashboard/AllocationChart";
import DashboardPositionsTable from "../components/dashboard/DashboardPositionsTable";
import PortfolioTrendChart from "../components/dashboard/PortfolioTrendChart";
import RecentActivityFeed from "../components/dashboard/RecentActivityFeed";
import WinnersLosersPanel from "../components/dashboard/WinnersLosersPanel";
import AuthAlert from "../components/auth/AuthAlert";
import DisplayMoney from "../components/portfolio/DisplayMoney";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import MoneyText from "../components/common/MoneyText";
import { useUser } from "../contexts/UserContext";
import { formatDateNl, formatEur } from "../utils/formatMoney";
import { getApiErrorMessage } from "../utils/apiError";
import { returnBasisLabel } from "../utils/valuationLabels";

function StatPill({
  label,
  amount,
  sub,
  tone,
}: {
  label: string;
  amount: string;
  sub?: string;
  tone?: "positive" | "negative" | "default";
}) {
  return (
    <Box
      px={3}
      py={2}
      bg="paper"
      border="1px solid"
      borderColor="line.soft"
      borderRadius="base"
      minW={{ base: "full", sm: "140px" }}
    >
      <Kicker mb={1}>{label}</Kicker>
      <DisplayMoney amount={amount} size="sm" signed tone={tone} />
      {sub && (
        <Text fontSize="xs" color="taupe.500" mt={0.5}>
          {sub}
        </Text>
      )}
    </Box>
  );
}

export default function DashboardPage() {
  const { user } = useUser();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [peildatum, setPeildatum] = useState<PeildatumSnapshot | null>(null);
  const [forfaitair, setForfaitair] = useState<ForfaitairBox3Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [snapshotBusy, setSnapshotBusy] = useState(false);
  const [error, setError] = useState("");
  const [snapshotMessage, setSnapshotMessage] = useState("");

  const [taxYear, setTaxYear] = useState(relevantTaxYear());
  const [taxYearRule, setTaxYearRule] = useState("");

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
      setTaxYearRule(ctx.rule);
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
  const todayLabel = formatDateNl(new Date().toISOString());
  const totalValue = summary?.total_value_eur ?? "0";
  const hasPositions = (summary?.positions_count ?? 0) > 0;
  return (
    <VStack align="stretch" spacing={5}>
      {error && <AuthAlert tone="error">{error}</AuthAlert>}

      <Grid
        templateColumns={{ base: "1fr", lg: "1fr 320px" }}
        gap={4}
        alignItems="stretch"
      >
        <FiscalCard p={{ base: 4, md: 5 }}>
          <Flex justify="space-between" align="flex-start" gap={3} flexWrap="wrap" mb={2}>
            <Kicker>
              Overzicht · <Box as="span" color="taupe.500">{todayLabel}</Box>
            </Kicker>
          </Flex>
          <Text
            fontFamily="heading"
            fontStyle="italic"
            fontSize="sm"
            color="ink.dim"
            mb={1}
          >
            Welkom terug, {greetingName}
          </Text>

          {loading ? (
            <Text color="ink.dim" fontSize="sm">
              Gegevens laden…
            </Text>
          ) : (
            <>
              <DisplayMoney amount={totalValue} size="md" />
              {summary?.hero_delta_30d?.available && (
                <Text fontSize="sm" color="ink.dim" mt={1}>
                  <Box
                    as="span"
                    color={
                      parseFloat(summary.hero_delta_30d.change_eur ?? "0") >= 0
                        ? "moss.500"
                        : "rust.500"
                    }
                    fontWeight={600}
                  >
                    {parseFloat(summary.hero_delta_30d.change_eur ?? "0") >= 0 ? "+" : ""}
                    {formatEur(summary.hero_delta_30d.change_eur ?? "0")} (
                    {summary.hero_delta_30d.change_percent}%)
                  </Box>{" "}
                  in 30 dagen
                </Text>
              )}
              <Text fontSize="xs" color="taupe.500" mt={1} mb={3}>
                {summary?.valuation_note ??
                  "Waarde op basis van kostprijs — geen live koersen beschikbaar."}
              </Text>

              {(summary?.returns && parseFloat(summary.returns.invested_eur) > 0) ||
              (summary?.ytd?.available && hasPositions) ? (
                <HStack spacing={2} flexWrap="wrap" align="stretch">
                  {summary?.returns && parseFloat(summary.returns.invested_eur) > 0 && (
                    <StatPill
                      label="Onrealiseerd"
                      amount={summary.returns.unrealized_return_eur}
                      sub={`${summary.returns.unrealized_return_percent}% · ${returnBasisLabel(summary.returns.method)}`}
                      tone={
                        parseFloat(summary.returns.unrealized_return_eur) >= 0
                          ? "positive"
                          : "negative"
                      }
                    />
                  )}
                  {summary?.ytd?.available && (
                    <StatPill
                      label={`YTD ${summary.ytd.year}`}
                      amount={summary.ytd.ytd_return_eur ?? "0"}
                      sub={`${summary.ytd.ytd_return_percent}% · t.o.v. ${formatEur(summary.ytd.start_value_eur ?? "0")}`}
                      tone={
                        parseFloat(summary.ytd.ytd_return_eur ?? "0") >= 0
                          ? "positive"
                          : "negative"
                      }
                    />
                  )}
                </HStack>
              ) : hasPositions ? (
                <Text fontSize="xs" color="ink.dim">
                  Voeg transacties toe om rendement te berekenen
                </Text>
              ) : null}
            </>
          )}
        </FiscalCard>

        <FiscalCard p={{ base: 4, md: 5 }} display="flex" flexDirection="column">
          <Kicker mb={2}>Belasting {taxYear}</Kicker>
          {taxYearRule && (
            <Text fontSize="xs" color="taupe.500" mb={2} lineHeight={1.4} noOfLines={2}>
              {taxYearRule}
            </Text>
          )}
          <Text fontSize="xs" color="ink.dim" mb={1}>
            Te betalen (forfaitair)
          </Text>
          {forfaitair?.available && forfaitair.tax_due_eur ? (
            <DisplayMoney amount={forfaitair.tax_due_eur} size="sm" tone="accent" />
          ) : (
            <MoneyText variant="display" fontSize="32px" color="ink.dim">
              —
            </MoneyText>
          )}
          <Text color="ink.dim" fontSize="xs" mt={2} lineHeight={1.5} flex={1}>
            {forfaitair?.available
              ? (forfaitair.disclaimer ?? "Box 3 op basis van peildatum.")
              : forfaitair?.message
                ? forfaitair.message
                : hasPositions
                  ? `Leg peildatum ${taxYear} vast voor Box 3.`
                  : "Koppel een platform om te starten."}
          </Text>
          {peildatum && (
            <Text fontSize="xs" color="taupe.500" mt={1}>
              Snapshot {formatEur(peildatum.total_value_eur)}
            </Text>
          )}
          <HStack mt={3} spacing={2} flexWrap="wrap">
            {forfaitair?.available && (
              <Button as={RouterLink} to="/belasting" variant="fiscalOutline" size="sm">
                Belastingpositie
              </Button>
            )}
            {hasPositions && !peildatum && (
              <Button
                variant="fiscal"
                size="sm"
                isLoading={snapshotBusy}
                onClick={() => void handleCreatePeildatum()}
              >
                Peildatum vastleggen
              </Button>
            )}
          </HStack>
          {snapshotMessage && (
            <Text fontSize="xs" color="taupe.500" mt={1}>
              {snapshotMessage}
            </Text>
          )}
        </FiscalCard>
      </Grid>

      {!loading && !hasPositions && (
        <FiscalCard p={5}>
          <Text fontFamily="heading" fontStyle="italic" color="ink.dim" fontSize="sm" mb={3}>
            Nog geen posities. Koppel een broker of voeg handmatig assets toe.
          </Text>
          <HStack spacing={2} flexWrap="wrap">
            <Button as={RouterLink} to="/platforms" variant="fiscal" size="sm">
              Platform koppelen
            </Button>
            <Button as={RouterLink} to="/portfolio/manual/asset" variant="fiscalOutline" size="sm">
              Asset toevoegen
            </Button>
          </HStack>
        </FiscalCard>
      )}

      {hasPositions && summary && (
        <>
          <SimpleGrid columns={{ base: 1, xl: 2 }} spacing={4}>
            <FiscalCard p={4}>
              <Kicker mb={2}>Waarde vs inleg (12 maanden)</Kicker>
              <PortfolioTrendChart
                points={summary.value_history ?? []}
                valuationNote={summary.valuation_note}
              />
            </FiscalCard>

            {summary.movers && Object.keys(summary.movers).length > 0 && (
              <FiscalCard p={4}>
                <Kicker mb={2}>Winnaars & verliezers</Kicker>
                <WinnersLosersPanel movers={summary.movers} />
              </FiscalCard>
            )}

            {summary.by_category.length > 0 && (
              <FiscalCard p={4}>
                <Kicker mb={2}>Verdeling</Kicker>
                <AllocationChart
                  categories={summary.by_category}
                  totalLabel={formatEur(summary.total_value_eur)}
                />
              </FiscalCard>
            )}
          </SimpleGrid>

          <SimpleGrid columns={{ base: 1, xl: 2 }} spacing={4}>
            <Box>
              <Flex justify="space-between" align="center" mb={2}>
                <Kicker>Posities · {summary.positions_count}</Kicker>
                <Link as={RouterLink} to="/portfolio" fontSize="xs" color="azure.500">
                  Portefeuille →
                </Link>
              </Flex>
              <DashboardPositionsTable
                positions={summary.positions}
                totalCount={summary.positions_count}
              />
            </Box>

            <Box>
              <Flex justify="space-between" align="center" mb={2}>
                <Kicker>Recente activiteit</Kicker>
                <Link as={RouterLink} to="/transactions" fontSize="xs" color="azure.500">
                  Alle transacties →
                </Link>
              </Flex>
              <RecentActivityFeed items={summary.recent_activity ?? []} />
            </Box>
          </SimpleGrid>

          {summary.platforms.length > 0 && (
            <FiscalCard p={3}>
              <Kicker mb={2}>Platformen · {summary.platforms.length}</Kicker>
              <Flex gap={2} flexWrap="wrap">
                {summary.platforms.map((platform) => (
                  <Box
                    key={platform.id}
                    px={3}
                    py={2}
                    bg="paper"
                    border="1px solid"
                    borderColor="line.soft"
                    borderRadius="base"
                    fontSize="sm"
                  >
                    <Text fontWeight={600}>{platform.display_name}</Text>
                    <Text fontSize="xs" color="taupe.500">
                      {platform.platform_display}
                    </Text>
                  </Box>
                ))}
              </Flex>
            </FiscalCard>
          )}
        </>
      )}
    </VStack>
  );
}
