import { FormEvent, useEffect, useState } from "react";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Select,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useLocation, useNavigate } from "react-router-dom";

import {
  createManualTransaction,
  listAssets,
  listPortfolios,
  type Portfolio,
} from "../api/portfolio";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { getApiErrorMessage } from "../utils/apiError";

const TX_TYPES = [
  { value: "buy", label: "Aankoop" },
  { value: "sell", label: "Verkoop" },
  { value: "dividend", label: "Dividend" },
  { value: "deposit", label: "Storting" },
  { value: "withdrawal", label: "Opname" },
];

export default function AddManualTransactionPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [assets, setAssets] = useState<{ id: number; label: string }[]>([]);
  const [assetId, setAssetId] = useState("");
  const [transactionType, setTransactionType] = useState("buy");
  const [quantity, setQuantity] = useState("");
  const [priceEur, setPriceEur] = useState("");
  const [occurredAt, setOccurredAt] = useState("");
  const [error, setError] = useState("");
  const message =
    (location.state as { message?: string } | null)?.message ?? "";
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void loadData();
  }, []);

  async function loadData() {
    try {
      const portfolios = await listPortfolios();
      const p = portfolios.find((row) => row.is_default) ?? portfolios[0] ?? null;
      setPortfolio(p);
      const assetRows = await listAssets();
      const options = assetRows.map((asset) => ({
        id: asset.id,
        label: `${asset.symbol} — ${asset.name || asset.symbol}`,
      }));
      setAssets(options);
      if (options.length > 0) {
        setAssetId(String(options[0].id));
      }
    } catch {
      setAssets([]);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!portfolio) {
      setError("Geen portefeuille gevonden.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createManualTransaction(portfolio.id, {
        asset_id: Number(assetId),
        transaction_type: transactionType,
        quantity,
        price_eur: priceEur || null,
        occurred_at: occurredAt ? new Date(occurredAt).toISOString() : undefined,
      });
      void navigate("/dashboard", {
        state: { message: "Transactie toegevoegd." },
      });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Transactie toevoegen mislukt."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <VStack align="stretch" spacing={8} maxW="lg">
      <Box>
        <Kicker mb={2}>Portefeuille</Kicker>
        <Heading size="lg">Transactie handmatig toevoegen</Heading>
      </Box>

      {message && <AuthAlert tone="success">{message}</AuthAlert>}
      {error && <AuthAlert tone="error">{error}</AuthAlert>}

      {assets.length === 0 && (
        <AuthAlert tone="info">
          Voeg eerst een asset toe via{" "}
          <Box as={RouterLink} to="/portfolio/manual/asset" color="azure.500">
            asset toevoegen
          </Box>
          .
        </AuthAlert>
      )}

      <FiscalCard p={6} as="form" onSubmit={(event) => void handleSubmit(event)}>
        <VStack align="stretch" spacing={4}>
          <FormControl isRequired>
            <FormLabel>Asset</FormLabel>
            <Select value={assetId} onChange={(e) => setAssetId(e.target.value)}>
              {assets.map((asset) => (
                <option key={asset.id} value={asset.id}>
                  {asset.label}
                </option>
              ))}
            </Select>
            <Text fontSize="xs" color="ink.dim" mt={1}>
              Gebaseerd op posities in uw portefeuille. Nieuw symbol?{" "}
              <Box as={RouterLink} to="/portfolio/manual/asset" color="azure.500">
                Asset toevoegen
              </Box>
            </Text>
          </FormControl>
          <FormControl>
            <FormLabel>Type</FormLabel>
            <Select
              value={transactionType}
              onChange={(e) => setTransactionType(e.target.value)}
            >
              {TX_TYPES.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
          </FormControl>
          <FormControl isRequired>
            <FormLabel>Aantal</FormLabel>
            <Input
              type="number"
              step="any"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
            />
          </FormControl>
          <FormControl>
            <FormLabel>Prijs per stuk (EUR)</FormLabel>
            <Input
              type="number"
              step="any"
              value={priceEur}
              onChange={(e) => setPriceEur(e.target.value)}
            />
          </FormControl>
          <FormControl>
            <FormLabel>Datum</FormLabel>
            <Input
              type="datetime-local"
              value={occurredAt}
              onChange={(e) => setOccurredAt(e.target.value)}
            />
          </FormControl>
          <Button
            type="submit"
            variant="fiscal"
            isLoading={loading}
            isDisabled={assets.length === 0}
          >
            Transactie opslaan
          </Button>
          <Button as={RouterLink} to="/portfolio" variant="fiscalOutline" size="sm">
            Annuleren
          </Button>
        </VStack>
      </FiscalCard>
    </VStack>
  );
}
