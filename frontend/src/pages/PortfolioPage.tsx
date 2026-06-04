import { useEffect, useState } from "react";
import {
  Button,
  Select,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import {
  getDashboardSummary,
  getPortfolio,
  listPortfolios,
  updateAssetCategory,
  type DashboardSummary,
  type Portfolio,
} from "../api/portfolio";
import AuthAlert from "../components/auth/AuthAlert";
import AllocationChart from "../components/dashboard/AllocationChart";
import InsightGrid from "../components/dashboard/InsightGrid";
import PortfolioTrendChart from "../components/dashboard/PortfolioTrendChart";
import FiscalCard from "../components/common/FiscalCard";
import FiscalNote from "../components/common/FiscalNote";
import FiscalTable from "../components/common/FiscalTable";
import SectionHeader from "../components/common/SectionHeader";
import PositionPnLTable from "../components/portfolio/PositionPnLTable";
import MotionSection from "../components/layout/MotionSection";
import PageHeader from "../components/layout/PageHeader";
import PageShell from "../components/layout/PageShell";
import { formatEur } from "../utils/formatMoney";
import { getApiErrorMessage } from "../utils/apiError";
import { positionPriceHint } from "../utils/valuationLabels";

const FISCALE_CATEGORIES: { value: string; label: string }[] = [
  { value: "belegging", label: "Belegging" },
  { value: "banktegoed", label: "Banktegoed" },
  { value: "edelmetaal", label: "Edelmetaal" },
  { value: "schuld", label: "Schuld" },
  { value: "overig", label: "Overig" },
];

export default function PortfolioPage() {
  const [, setPortfolios] = useState<Portfolio[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [categoryBusyId, setCategoryBusyId] = useState<number | null>(null);
  const [categoryNote, setCategoryNote] = useState("");

  useEffect(() => {
    void loadPortfolio();
  }, []);

  async function loadPortfolio() {
    setLoading(true);
    setError("");
    try {
      const [portfolioRows, summaryData] = await Promise.all([
        listPortfolios(),
        getDashboardSummary(),
      ]);
      setPortfolios(portfolioRows);
      setSummary(summaryData);
      const defaultP = portfolioRows.find((p) => p.is_default) ?? portfolioRows[0];
      if (defaultP) {
        const detail = await getPortfolio(defaultP.id);
        setDetailPositions(detail.positions);
      }
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Portefeuille laden mislukt."));
    } finally {
      setLoading(false);
    }
  }

  const [detailPositions, setDetailPositions] = useState<
    Awaited<ReturnType<typeof getPortfolio>>["positions"]
  >([]);

  async function handleCategoryChange(assetId: number, category: string) {
    setCategoryBusyId(assetId);
    setCategoryNote("");
    setError("");
    try {
      await updateAssetCategory(assetId, category);
      setCategoryNote("Categorie opgeslagen. Herbereken peildatum indien nodig.");
      await loadPortfolio();
    } catch (categoryError) {
      setError(getApiErrorMessage(categoryError, "Categorie bijwerken mislukt."));
    } finally {
      setCategoryBusyId(null);
    }
  }

  const platformCount = summary?.platforms.length ?? 0;
  const hasPositions = (summary?.positions_count ?? 0) > 0;

  return (
    <PageShell>
      <MotionSection>
        <PageHeader
          kicker={`Alle posities · ${platformCount} platformen`}
          title={
            <>
              Portefeuille — <Text as="em">alle posities</Text>
            </>
          }
          subtitle="Al uw beleggingen gecombineerd uit gekoppelde platformen, met inzichten per positie: aankoopprijs, rendement en verdeling."
          actions={
            <>
              <Button as={RouterLink} to="/portfolio/manual/asset" variant="fiscalOutline" size="sm">
                Asset toevoegen
              </Button>
              <Button as={RouterLink} to="/portfolio/manual/transaction" variant="fiscal" size="sm">
                Transactie toevoegen
              </Button>
            </>
          }
        />
      </MotionSection>

      {error && (
        <MotionSection>
          <AuthAlert tone="error">{error}</AuthAlert>
        </MotionSection>
      )}
      {categoryNote && (
        <MotionSection>
          <AuthAlert tone="info">{categoryNote}</AuthAlert>
        </MotionSection>
      )}

      {loading ? (
        <Text color="ink.dim" fontStyle="italic">
          Portefeuille laden…
        </Text>
      ) : !hasPositions || !summary ? (
        <MotionSection>
          <FiscalCard elevated p={8} textAlign="center">
            <Text fontFamily="heading" fontStyle="italic" color="ink.dim" mb={5}>
              Nog geen posities — koppel een platform of voeg handmatig assets toe.
            </Text>
            <Button as={RouterLink} to="/platforms" variant="fiscal">
              Platform koppelen
            </Button>
          </FiscalCard>
        </MotionSection>
      ) : (
        <>
          <MotionSection>
            <SectionHeader
              title={
                <>
                  Portefeuille <Text as="em">inzichten</Text>
                </>
              }
              kicker="all-time · alle platformen"
            />
            <InsightGrid summary={summary} />
          </MotionSection>

          {summary.by_category.length > 0 && (
            <MotionSection>
              <SectionHeader
                title={
                  <>
                    Portefeuille-<Text as="em">samenstelling</Text>
                  </>
                }
                kicker="alle posities · per assetklasse"
              />
              <FiscalCard elevated p={{ base: 4, md: 6 }}>
                <AllocationChart
                  categories={summary.by_category}
                  totalLabel={formatEur(summary.total_value_eur)}
                />
              </FiscalCard>
            </MotionSection>
          )}

          {(summary.value_history?.length ?? 0) > 0 && (
            <MotionSection>
              <SectionHeader
                title={
                  <>
                    Waarde <Text as="em">vs. kostprijs</Text>
                  </>
                }
                kicker="afgelopen 12 maanden · marktwaarde tegenover kostprijs"
              />
              <FiscalCard elevated p={{ base: 4, md: 6 }}>
                <PortfolioTrendChart
                  points={summary.value_history ?? []}
                  valuationNote={summary.valuation_note}
                />
              </FiscalCard>
            </MotionSection>
          )}

          <MotionSection>
            <SectionHeader
              title={
                <>
                  Winst & verlies <Text as="em">per positie</Text>
                </>
              }
              kicker="kostprijs vs. marktwaarde · gesorteerd op winst/verlies"
            />
            <FiscalCard elevated p={5}>
              <PositionPnLTable dashboardPositions={summary.positions} />
            </FiscalCard>
          </MotionSection>

          <MotionSection>
            <SectionHeader
              title={
                <>
                  Alle <Text as="em">posities</Text>
                </>
              }
              kicker={`${summary.positions_count} posities · fiscale categorie`}
            />
            <FiscalNote mb={4}>
              Wijzig de Box 3-categorie per asset. Leg daarna uw peildatum opnieuw vast op de
              belastingpagina.
            </FiscalNote>
            <FiscalTable>
              <Thead>
                <Tr>
                  <Th>Asset</Th>
                  <Th>Categorie</Th>
                  <Th isNumeric>Aantal</Th>
                  <Th>Koers</Th>
                  <Th isNumeric>Waarde</Th>
                </Tr>
              </Thead>
              <Tbody>
                {summary.positions.map((position) => (
                  <Tr key={position.id}>
                    <Td>
                      <Text fontWeight={600}>{position.symbol}</Text>
                      <Text fontSize="xs" color="ink.dim">
                        {position.name}
                      </Text>
                    </Td>
                    <Td>
                      {position.asset_id != null ? (
                        <Select
                          size="sm"
                          value={position.category ?? "belegging"}
                          isDisabled={categoryBusyId === position.asset_id}
                          onChange={(e) =>
                            void handleCategoryChange(position.asset_id!, e.target.value)
                          }
                        >
                          {FISCALE_CATEGORIES.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </Select>
                      ) : (
                        <Text fontSize="sm" color="ink.dim">
                          {position.category_label}
                        </Text>
                      )}
                    </Td>
                    <Td isNumeric>{position.quantity}</Td>
                    <Td fontSize="sm" color="ink.dim">
                      {positionPriceHint(position) ?? "—"}
                    </Td>
                    <Td isNumeric fontWeight={500}>
                      {formatEur(position.value_eur)}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </FiscalTable>
          </MotionSection>

          <MotionSection>
            <SectionHeader
              title={
                <>
                  Betaalde fees <Text as="em">per platform</Text>
                </>
              }
              kicker="premium · YTD (binnenkort)"
            />
            <FiscalCard elevated p={5}>
              <Text fontSize="sm" color="ink.dim" lineHeight={1.7}>
                Fee-tracking per platform wordt binnenkort toegevoegd. U ziet dan transactie- en
                beheerkosten uitgesplitst zoals in het premium prototype.
              </Text>
            </FiscalCard>
          </MotionSection>
        </>
      )}
    </PageShell>
  );
}
