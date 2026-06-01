import { useCallback, useEffect, useState } from "react";
import {
  Button,
  Flex,
  FormControl,
  FormLabel,
  Grid,
  Input,
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
  downloadPortfolioTransactionsCsv,
  getDashboardSummary,
  getPortfolioTransactions,
  type Transaction,
  type TransactionListParams,
} from "../api/portfolio";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import FiscalTable from "../components/common/FiscalTable";
import InsightCard from "../components/common/InsightCard";
import SectionHeader from "../components/common/SectionHeader";
import MotionSection from "../components/layout/MotionSection";
import PageHeader from "../components/layout/PageHeader";
import PageShell from "../components/layout/PageShell";
import { formatDateNl, formatEur } from "../utils/formatMoney";
import { formatQuantity } from "../utils/formatQuantity";
import { platformLabel } from "../utils/platformLabels";
import { getApiErrorMessage } from "../utils/apiError";

const TX_LABELS: Record<string, string> = {
  buy: "Aankoop",
  sell: "Verkoop",
  dividend: "Dividend",
  deposit: "Storting",
  withdrawal: "Opname",
  fee: "Kosten",
  other: "Overig",
};

const PAGE_SIZE = 20;

type SortField =
  | "occurred_at"
  | "symbol"
  | "transaction_type"
  | "source_platform"
  | "quantity"
  | "price_eur";

const SORT_COLUMNS: { key: SortField; label: string; align?: "right" }[] = [
  { key: "occurred_at", label: "Datum" },
  { key: "symbol", label: "Asset" },
  { key: "transaction_type", label: "Type" },
  { key: "source_platform", label: "Platform" },
  { key: "quantity", label: "Aantal", align: "right" },
  { key: "price_eur", label: "Prijs", align: "right" },
];

const selectSx = {
  bg: "paper",
  border: "1px solid",
  borderColor: "line.DEFAULT",
  borderRadius: "base",
  fontSize: "body",
  h: "42px",
  _hover: { borderColor: "taupe.500" },
  _focusVisible: { borderColor: "azure.500", boxShadow: "none" },
};

export default function TransactionsPage() {
  const [portfolioId, setPortfolioId] = useState<number | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterOptions, setFilterOptions] = useState<{
    platforms: string[];
    transaction_types: string[];
  }>({ platforms: [], transaction_types: [] });

  const [platform, setPlatform] = useState("");
  const [transactionType, setTransactionType] = useState("");
  const [symbol, setSymbol] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sort, setSort] = useState<SortField>("occurred_at");
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exportBusy, setExportBusy] = useState(false);

  const loadTransactions = useCallback(
    async (targetPage: number) => {
      if (!portfolioId) {
        setTransactions([]);
        setTotal(0);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError("");
      try {
        const params: TransactionListParams = {
          page: targetPage,
          page_size: PAGE_SIZE,
          sort,
          order,
        };
        if (platform) params.platform = platform;
        if (transactionType) params.transaction_type = transactionType;
        if (symbol.trim()) params.symbol = symbol.trim();
        if (dateFrom) params.date_from = dateFrom;
        if (dateTo) params.date_to = dateTo;

        const data = await getPortfolioTransactions(portfolioId, params);
        setTransactions(data.items);
        setTotal(data.total);
        setPage(data.page);
        setTotalPages(data.total_pages);
        setFilterOptions({
          platforms: data.filters.platforms,
          transaction_types: data.filters.transaction_types,
        });
      } catch (loadError) {
        setError(getApiErrorMessage(loadError, "Transacties laden mislukt."));
      } finally {
        setLoading(false);
      }
    },
    [portfolioId, sort, order, platform, transactionType, symbol, dateFrom, dateTo],
  );

  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        const summary = await getDashboardSummary();
        setPortfolioId(summary.portfolio_id ?? null);
      } catch (loadError) {
        setError(getApiErrorMessage(loadError, "Portefeuille laden mislukt."));
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (portfolioId === null && !error) return;
    void loadTransactions(1);
  }, [portfolioId, loadTransactions]);

  function handleSort(field: SortField) {
    if (sort === field) {
      setOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSort(field);
      setOrder(field === "occurred_at" ? "desc" : "asc");
    }
  }

  function handleApplyFilters() {
    void loadTransactions(1);
  }

  function currentFilterParams(): TransactionListParams {
    return {
      sort,
      order,
      platform: platform || undefined,
      transaction_type: transactionType || undefined,
      symbol: symbol || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    };
  }

  async function handleExportCsv() {
    if (!portfolioId) return;
    setExportBusy(true);
    setError("");
    try {
      await downloadPortfolioTransactionsCsv(portfolioId, currentFilterParams());
    } catch (exportError) {
      setError(getApiErrorMessage(exportError, "CSV-export mislukt."));
    } finally {
      setExportBusy(false);
    }
  }

  function handleResetFilters() {
    setPlatform("");
    setTransactionType("");
    setSymbol("");
    setDateFrom("");
    setDateTo("");
    setSort("occurred_at");
    setOrder("desc");
  }

  function sortIndicator(field: SortField): string {
    if (sort !== field) return "";
    return order === "asc" ? " ↑" : " ↓";
  }

  const rangeStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const rangeEnd = Math.min(page * PAGE_SIZE, total);

  return (
    <PageShell>
      <MotionSection>
        <PageHeader
          kicker="Transacties"
          title={
            <>
              Transactie<Text as="em">historie</Text>
            </>
          }
          subtitle="Alle transacties uit uw standaardportefeuille. Filter, sorteer en exporteer naar CSV."
          actions={
            <>
              <Button
                variant="fiscalOutline"
                size="sm"
                isLoading={exportBusy}
                isDisabled={!portfolioId || total === 0}
                onClick={() => void handleExportCsv()}
              >
                Exporteer CSV
              </Button>
              <Button
                as={RouterLink}
                to="/portfolio/manual/transaction"
                variant="fiscal"
                size="sm"
              >
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

      {!loading && total > 0 && (
        <MotionSection>
          <Grid templateColumns={{ base: "1fr", sm: "repeat(2, 1fr)" }} gap={4}>
            <InsightCard
              label="Totaal transacties"
              value={String(total)}
              delta={`pagina ${page} van ${totalPages}`}
            />
            <InsightCard
              label="Weergave"
              value={`${rangeStart}–${rangeEnd}`}
              delta="huidige selectie"
              accent="ochre"
            />
          </Grid>
        </MotionSection>
      )}

      <MotionSection>
        <SectionHeader title="Filters" kicker="verfijn uw overzicht" />
        <FiscalCard elevated p={5}>
          <Grid
            templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" }}
            gap={4}
          >
            <FormControl>
              <FormLabel fontSize="sm" color="ink.dim">
                Platform
              </FormLabel>
              <Select
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                sx={selectSx}
              >
                <option value="">Alle platformen</option>
                {filterOptions.platforms.map((p) => (
                  <option key={p} value={p}>
                    {platformLabel(p)}
                  </option>
                ))}
              </Select>
            </FormControl>
            <FormControl>
              <FormLabel fontSize="sm" color="ink.dim">
                Type
              </FormLabel>
              <Select
                value={transactionType}
                onChange={(e) => setTransactionType(e.target.value)}
                sx={selectSx}
              >
                <option value="">Alle types</option>
                {filterOptions.transaction_types.map((t) => (
                  <option key={t} value={t}>
                    {TX_LABELS[t] ?? t}
                  </option>
                ))}
              </Select>
            </FormControl>
            <FormControl>
              <FormLabel fontSize="sm" color="ink.dim">
                Asset (symbool)
              </FormLabel>
              <Input
                variant="fiscal"
                placeholder="bijv. BTC"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleApplyFilters();
                }}
              />
            </FormControl>
            <FormControl>
              <FormLabel fontSize="sm" color="ink.dim">
                Vanaf datum
              </FormLabel>
              <Input
                type="date"
                variant="fiscal"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </FormControl>
            <FormControl>
              <FormLabel fontSize="sm" color="ink.dim">
                Tot datum
              </FormLabel>
              <Input
                type="date"
                variant="fiscal"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </FormControl>
          </Grid>
          <Flex gap={2} mt={5} flexWrap="wrap">
            <Button variant="fiscal" size="sm" onClick={handleApplyFilters}>
              Toepassen
            </Button>
            <Button variant="fiscalOutline" size="sm" onClick={handleResetFilters}>
              Wis filters
            </Button>
          </Flex>
        </FiscalCard>
      </MotionSection>

      <MotionSection>
        <SectionHeader
          title={
            <>
              Resultaten <Text as="em">tabel</Text>
            </>
          }
          kicker="klik op kolomkop om te sorteren"
        />
        {loading ? (
          <Text color="ink.dim" fontSize="sm" fontStyle="italic">
            Transacties laden…
          </Text>
        ) : total === 0 ? (
          <FiscalCard elevated p={8} textAlign="center">
            <Text fontFamily="heading" fontStyle="italic" color="ink.dim" lineHeight={1.7} mb={5}>
              Geen transacties gevonden voor deze selectie.
            </Text>
            <Button as={RouterLink} to="/platforms" variant="fiscal" size="sm">
              Naar Mijn platformen
            </Button>
          </FiscalCard>
        ) : (
          <FiscalTable
            toolbar={
              <Flex justify="space-between" align="center" flexWrap="wrap" gap={2}>
                <Text fontSize="sm" color="ink.dim">
                  {rangeStart}–{rangeEnd} van {total} transacties
                </Text>
                <Flex gap={2}>
                  <Button
                    variant="fiscalOutline"
                    size="sm"
                    isDisabled={page <= 1}
                    onClick={() => void loadTransactions(page - 1)}
                  >
                    Vorige
                  </Button>
                  <Text fontSize="sm" color="ink.dim" alignSelf="center" px={1}>
                    Pagina {page} / {totalPages}
                  </Text>
                  <Button
                    variant="fiscalOutline"
                    size="sm"
                    isDisabled={page >= totalPages}
                    onClick={() => void loadTransactions(page + 1)}
                  >
                    Volgende
                  </Button>
                </Flex>
              </Flex>
            }
          >
            <Thead>
              <Tr>
                {SORT_COLUMNS.map((col) => (
                  <Th
                    key={col.key}
                    isNumeric={col.align === "right"}
                    cursor="pointer"
                    userSelect="none"
                    onClick={() => handleSort(col.key)}
                    _hover={{ color: "azure.500" }}
                    whiteSpace="nowrap"
                  >
                    {col.label}
                    {sortIndicator(col.key)}
                  </Th>
                ))}
              </Tr>
            </Thead>
            <Tbody>
              {transactions.map((tx) => (
                <Tr key={tx.id}>
                  <Td whiteSpace="nowrap">{formatDateNl(tx.occurred_at)}</Td>
                  <Td fontWeight={600}>{tx.asset.symbol}</Td>
                  <Td>{TX_LABELS[tx.transaction_type] ?? tx.transaction_type}</Td>
                  <Td color="ink.dim">{platformLabel(tx.source_platform)}</Td>
                  <Td isNumeric>{formatQuantity(tx.quantity)}</Td>
                  <Td isNumeric>
                    {tx.price_eur ? formatEur(tx.price_eur) : "—"}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </FiscalTable>
        )}
      </MotionSection>
    </PageShell>
  );
}
