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

import { getDashboardSummary, type DashboardPosition } from "../api/portfolio";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { formatEur } from "../utils/formatMoney";
import { getApiErrorMessage } from "../utils/apiError";

export default function PortfolioPage() {
  const [positions, setPositions] = useState<DashboardPosition[]>([]);
  const [total, setTotal] = useState("0");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void loadPortfolio();
  }, []);

  async function loadPortfolio() {
    setLoading(true);
    setError("");
    try {
      const summary = await getDashboardSummary();
      setPositions(summary.positions);
      setTotal(summary.total_value_eur);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Portefeuille laden mislukt."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <VStack align="stretch" spacing={8}>
      <Box>
        <Kicker mb={2}>Portefeuille</Kicker>
        <Heading size="lg">Alle posities</Heading>
        <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
          Waarden op kostprijs. Marktwaarden en rendement per positie volgen in latere fases.
        </Text>
      </Box>

      {error && <AuthAlert tone="error">{error}</AuthAlert>}

      <FiscalCard p={5}>
        <Kicker mb={1}>Totaal (kostprijs)</Kicker>
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
            Geen posities gevonden. Laad voorbeelddata of koppel een platform.
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
                  <Th>Asset</Th>
                  <Th>Categorie</Th>
                  <Th isNumeric>Aantal</Th>
                  <Th isNumeric>Waarde</Th>
                </Tr>
              </Thead>
              <Tbody>
                {positions.map((position) => (
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
                    <Td isNumeric fontWeight={500}>
                      {formatEur(position.value_eur)}
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
