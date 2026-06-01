import { useEffect, useState } from "react";
import {
  Box,
  Button,
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
import { Link as RouterLink } from "react-router-dom";

import {
  getDashboardSummary,
  getPortfolioTransactions,
  type Transaction,
} from "../api/portfolio";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { formatDateNl, formatEur } from "../utils/formatMoney";
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

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void loadTransactions();
  }, []);

  async function loadTransactions() {
    setLoading(true);
    setError("");
    try {
      const summary = await getDashboardSummary();
      if (!summary.portfolio_id) {
        setTransactions([]);
        return;
      }
      const data = await getPortfolioTransactions(summary.portfolio_id);
      setTransactions(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Transacties laden mislukt."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <VStack align="stretch" spacing={8}>
      <Box>
        <Kicker mb={2}>Transacties</Kicker>
        <Heading size="lg">Transactiehistorie</Heading>
        <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
          Laatste transacties uit uw standaardportefeuille (sync en demo).
        </Text>
      </Box>

      {error && <AuthAlert tone="error">{error}</AuthAlert>}

      {loading ? (
        <Text color="ink.dim" fontSize="sm">
          Transacties laden…
        </Text>
      ) : transactions.length === 0 ? (
        <FiscalCard p={6}>
          <Text color="ink.dim" lineHeight={1.7} mb={4}>
            Geen transacties gevonden.
          </Text>
          <Button as={RouterLink} to="/platforms" variant="fiscal" size="sm">
            Naar Mijn platformen
          </Button>
        </FiscalCard>
      ) : (
        <FiscalCard p={0} overflow="hidden">
          <Box overflowX="auto">
            <Table size="sm" variant="simple">
              <Thead bg="backgroundCard">
                <Tr>
                  <Th>Datum</Th>
                  <Th>Asset</Th>
                  <Th>Type</Th>
                  <Th>Platform</Th>
                  <Th isNumeric>Aantal</Th>
                  <Th isNumeric>Prijs</Th>
                </Tr>
              </Thead>
              <Tbody>
                {transactions.map((tx) => (
                  <Tr key={tx.id}>
                    <Td whiteSpace="nowrap">{formatDateNl(tx.occurred_at)}</Td>
                    <Td fontWeight={600}>{tx.asset.symbol}</Td>
                    <Td>{TX_LABELS[tx.transaction_type] ?? tx.transaction_type}</Td>
                    <Td color="ink.dim">{tx.source_platform || "—"}</Td>
                    <Td isNumeric>{tx.quantity}</Td>
                    <Td isNumeric>
                      {tx.price_eur ? formatEur(tx.price_eur) : "—"}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
        </FiscalCard>
      )}
    </VStack>
  );
}
