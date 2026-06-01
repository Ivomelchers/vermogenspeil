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
  listPortfolios,
  type DashboardPosition,
  type Portfolio,
} from "../api/portfolio";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { formatEur } from "../utils/formatMoney";
import { getApiErrorMessage } from "../utils/apiError";
import { positionPriceHint, valuationBasisLabel } from "../utils/valuationLabels";

export default function PortfolioPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [positions, setPositions] = useState<DashboardPosition[]>([]);
  const [total, setTotal] = useState("0");
  const [valuationMethod, setValuationMethod] = useState<
    "market" | "mixed" | "cost_basis"
  >("cost_basis");
  const [valuationNote, setValuationNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void loadPortfolio();
  }, []);

  async function loadPortfolio() {
    setLoading(true);
    setError("");
    try {
      const [portfolioRows, summary] = await Promise.all([
        listPortfolios(),
        getDashboardSummary(),
      ]);
      setPortfolios(portfolioRows);
      setPositions(summary.positions);
      setTotal(summary.total_value_eur);
      setValuationMethod(summary.valuation_method);
      setValuationNote(summary.valuation_note ?? "");
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Portefeuille laden mislukt."));
    } finally {
      setLoading(false);
    }
  }

  const basisLabel = valuationBasisLabel(valuationMethod);

  return (
    <VStack align="stretch" spacing={8}>
      <Box>
        <Kicker mb={2}>Portefeuille</Kicker>
        <Heading size="lg">Alle posities</Heading>
        <Box display="flex" gap={2} flexWrap="wrap" mt={4}>
          <Button as={RouterLink} to="/portfolio/manual/asset" variant="fiscalOutline" size="sm">
            Asset toevoegen
          </Button>
          <Button as={RouterLink} to="/portfolio/manual/transaction" variant="fiscalOutline" size="sm">
            Transactie toevoegen
          </Button>
        </Box>
        <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
          {valuationNote ||
            "Waarden op basis van kostprijs. Live koersen worden opgehaald zodra beschikbaar."}
        </Text>
      </Box>

      {error && <AuthAlert tone="error">{error}</AuthAlert>}

      {!loading && portfolios.length > 0 && (
        <FiscalCard p={5}>
          <Kicker mb={3}>Uw portefeuilles</Kicker>
          <VStack align="stretch" spacing={2}>
            {portfolios.map((row) => (
              <Box
                key={row.id}
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                flexWrap="wrap"
                gap={2}
                py={2}
                borderBottom="1px solid"
                borderColor="line.soft"
                _last={{ borderBottom: "none" }}
              >
                <Text fontWeight={row.is_default ? 600 : 400}>
                  {row.name}
                  {row.is_default && (
                    <Text as="span" fontSize="xs" color="ink.dim" ml={2}>
                      standaard
                    </Text>
                  )}
                </Text>
                <Text fontSize="sm" color="ink.dim">
                  {row.positions_count} posities · {row.transactions_count} transacties
                </Text>
              </Box>
            ))}
          </VStack>
        </FiscalCard>
      )}

      <FiscalCard p={5}>
        <Kicker mb={1}>Totaal ({basisLabel.toLowerCase()})</Kicker>
        <Text fontFamily="heading" fontSize="32px" letterSpacing="-0.02em">
          {formatEur(total)}
        </Text>
      </FiscalCard>

      {loading ? (
        <Text color="ink.dim" fontSize="sm">
          Posities laden…
        </Text>
      ) : positions.length === 0 ? (
        <FiscalCard p={6}>
          <Text color="ink.dim" lineHeight={1.7} mb={4}>
            Geen posities gevonden. Koppel een platform of voeg handmatig transacties toe.
          </Text>
          <Box display="flex" gap={2} flexWrap="wrap">
            <Button as={RouterLink} to="/platforms" variant="fiscal" size="sm">
              Platform koppelen
            </Button>
            <Button as={RouterLink} to="/portfolio/manual/transaction" variant="fiscalOutline" size="sm">
              Transactie toevoegen
            </Button>
          </Box>
        </FiscalCard>
      ) : (
        <FiscalCard p={0} overflow="hidden">
          <Box overflowX="auto">
            <Table size="sm" variant="simple">
              <Thead bg="backgroundCard">
                <Tr>
                  <Th>Asset</Th>
                  <Th>Categorie</Th>
                  <Th isNumeric>Aantal</Th>
                  <Th>Koers</Th>
                  <Th isNumeric>Waarde</Th>
                </Tr>
              </Thead>
              <Tbody>
                {positions.map((position) => {
                  const priceHint = positionPriceHint(position);
                  return (
                    <Tr key={position.id}>
                      <Td>
                        <Text fontWeight={600}>{position.symbol}</Text>
                        <Text fontSize="xs" color="ink.dim">
                          {position.name}
                        </Text>
                      </Td>
                      <Td color="ink.dim">{position.category_label}</Td>
                      <Td isNumeric sx={{ fontVariantNumeric: "tabular-nums" }}>
                        {position.quantity}
                      </Td>
                      <Td fontSize="sm" color="ink.dim">
                        {priceHint ?? "—"}
                      </Td>
                      <Td isNumeric fontWeight={500}>
                        {formatEur(position.value_eur)}
                      </Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          </Box>
        </FiscalCard>
      )}
    </VStack>
  );
}
