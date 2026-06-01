import { FormEvent, useState } from "react";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Select,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { createManualAsset } from "../api/portfolio";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { getApiErrorMessage } from "../utils/apiError";

const ASSET_TYPES = [
  { value: "stock", label: "Aandeel" },
  { value: "etf", label: "ETF" },
  { value: "crypto", label: "Crypto" },
  { value: "metal", label: "Edelmetaal" },
  { value: "cash", label: "Spaargeld" },
  { value: "fund", label: "Fonds" },
  { value: "other", label: "Overig" },
];

const CATEGORIES = [
  { value: "belegging", label: "Belegging" },
  { value: "banktegoed", label: "Banktegoed / sparen" },
  { value: "edelmetaal", label: "Edelmetaal" },
  { value: "schuld", label: "Schuld" },
  { value: "overig", label: "Overig" },
];

export default function AddManualAssetPage() {
  const navigate = useNavigate();
  const [symbol, setSymbol] = useState("");
  const [name, setName] = useState("");
  const [assetType, setAssetType] = useState("stock");
  const [category, setCategory] = useState("belegging");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await createManualAsset({
        symbol: symbol.trim(),
        name: name.trim(),
        asset_type: assetType,
        category,
      });
      void navigate("/portfolio/manual/transaction", {
        state: { message: "Asset toegevoegd. Voeg nu een transactie toe." },
      });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Asset toevoegen mislukt."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <VStack align="stretch" spacing={8} maxW="lg">
      <Box>
        <Kicker mb={2}>Portefeuille</Kicker>
        <Heading size="lg">Asset handmatig toevoegen</Heading>
      </Box>

      {error && <AuthAlert tone="error">{error}</AuthAlert>}

      <FiscalCard p={6} as="form" onSubmit={(event) => void handleSubmit(event)}>
        <VStack align="stretch" spacing={4}>
          <FormControl isRequired>
            <FormLabel>Symbool / ISIN</FormLabel>
            <Input value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="IWDA" />
          </FormControl>
          <FormControl>
            <FormLabel>Naam</FormLabel>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="iShares MSCI World" />
          </FormControl>
          <FormControl>
            <FormLabel>Type</FormLabel>
            <Select value={assetType} onChange={(e) => setAssetType(e.target.value)}>
              {ASSET_TYPES.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
          </FormControl>
          <FormControl>
            <FormLabel>Vermogenscategorie (Box 3)</FormLabel>
            <Select value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
          </FormControl>
          <Button type="submit" variant="fiscal" isLoading={loading}>
            Asset opslaan
          </Button>
          <Button as={RouterLink} to="/portfolio" variant="fiscalOutline" size="sm">
            Annuleren
          </Button>
        </VStack>
      </FiscalCard>
    </VStack>
  );
}
