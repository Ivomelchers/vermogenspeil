import { useMemo, useState } from "react";
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  Grid,
  Input,
  Link,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate, useSearchParams } from "react-router-dom";

import { connectBitvavo, pollSyncJob } from "../api/integrations";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import FiscalCard from "../components/common/FiscalCard";
import FiscalDisclaimer from "../components/common/FiscalDisclaimer";
import PlatformAvatar from "../components/platforms/PlatformAvatar";
import MotionSection from "../components/layout/MotionSection";
import PageHeader from "../components/layout/PageHeader";
import PageShell from "../components/layout/PageShell";
import {
  PLATFORM_CATALOG,
  type CatalogPlatform,
  type IntegrationMethod,
} from "../data/platformCatalog";
import { useUser } from "../contexts/UserContext";
import { getApiErrorMessage } from "../utils/apiError";

const METHOD_CARDS: {
  method: IntegrationMethod;
  icon: string;
  label: string;
  name: string;
  desc: string;
  platforms: string;
}[] = [
  {
    method: "api",
    icon: "⚡",
    label: "API-koppeling",
    name: "Realtime sync",
    desc: "Verbind direct met API-key. Data wordt automatisch en doorlopend bijgewerkt.",
    platforms: "Bitvavo, Coinbase, Bybit, Kraken, OKX, IBKR, Bitpanda",
  },
  {
    method: "csv",
    icon: "⤴",
    label: "CSV-upload",
    name: "Periodieke import",
    desc: "Upload zelf een transactie-export. Ideaal voor brokers zonder API.",
    platforms: "DEGIRO, eToro, Trading 212, BUX Zero",
  },
  {
    method: "year",
    icon: "⎘",
    label: "Jaaroverzicht (PDF)",
    name: "Jaarlijkse import",
    desc: "Upload het jaaroverzicht dat het platform verstrekt. Eenmaal per jaar.",
    platforms: "ABN AMRO, ING, Rabobank, Meesman",
  },
];

export default function AddPlatformPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useUser();

  const initialPlatform = searchParams.get("platform") ?? "";
  const initialMethod = (searchParams.get("method") as IntegrationMethod | null) ?? null;

  const [search, setSearch] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState<CatalogPlatform | null>(
    () => PLATFORM_CATALOG.find((p) => p.id === initialPlatform) ?? null,
  );
  const [selectedMethod, setSelectedMethod] = useState<IntegrationMethod | null>(initialMethod);

  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [label, setLabel] = useState("Bitvavo");
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const filteredPlatforms = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return PLATFORM_CATALOG.slice(0, 8);
    return PLATFORM_CATALOG.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.searchTerms?.includes(q) ||
        p.typeLabel.toLowerCase().includes(q),
    );
  }, [search]);

  const availableMethods = selectedPlatform?.methods ?? [];

  async function handleBitvavoSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setStatusMessage("");
    setIsSubmitting(true);
    try {
      setStatusMessage("Verbinding controleren…");
      const result = await connectBitvavo({
        api_key: apiKey.trim(),
        api_secret: apiSecret.trim(),
        label: label.trim() || "Bitvavo",
      });
      if (result.sync_job?.id) {
        setStatusMessage("Portfolio synchroniseren…");
        const job = await pollSyncJob(result.sync_job.id);
        if (job.status === "error") {
          setError(job.error_message || "Synchronisatie mislukt.");
          return;
        }
      }
      navigate("/platforms", {
        state: { message: "Bitvavo succesvol gekoppeld." },
      });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Bitvavo koppelen mislukt."));
    } finally {
      setIsSubmitting(false);
    }
  }

  const showBitvavoForm =
    selectedPlatform?.id === "bitvavo" && selectedMethod === "api";

  return (
    <PageShell maxW="960px">
      <MotionSection>
        <PageHeader
          kicker={
            <Link as={RouterLink} to="/platforms" color="azure.500" fontSize="inherit">
              ← Mijn platformen
            </Link>
          }
          title={
            <>
              Nieuwe <Text as="em">databron</Text>
            </>
          }
          subtitle="Voeg een broker, exchange of bank toe. Kies eerst het platform en vervolgens de koppelingsmethode die dat platform ondersteunt."
        />
      </MotionSection>

      {user && !user.email_verified && (
        <MotionSection>
          <AuthAlert tone="info">
            Bevestig eerst uw e-mailadres voordat u een platform kunt koppelen.
          </AuthAlert>
        </MotionSection>
      )}

      <MotionSection>
        <Text fontSize="sm" fontWeight={600} letterSpacing="0.06em" color="ink.dim" mb={3}>
          Stap 1 · Kies een platform
        </Text>
        <Input
          variant="fiscal"
          placeholder="Zoek platform… (bijv. DEGIRO, Bitvavo)"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          mb={4}
        />
        <SimpleGrid columns={{ base: 2, md: 4 }} spacing={3}>
          {filteredPlatforms.map((platform) => {
            const active = selectedPlatform?.id === platform.id;
            return (
              <Box
                key={platform.id}
                as="button"
                type="button"
                textAlign="left"
                p={4}
                border="1px solid"
                borderColor={active ? "azure.500" : "line.soft"}
                borderRadius="base"
                bg={active ? "azure.50" : "backgroundCard"}
                transition="all 0.15s"
                _hover={{ borderColor: "azure.400" }}
                onClick={() => {
                  setSelectedPlatform(platform);
                  setSelectedMethod(null);
                  if (platform.id === "bitvavo") setLabel("Bitvavo");
                }}
              >
                <Flex gap={3} align="center">
                  <PlatformAvatar initials={platform.initials} color={platform.color} size="sm" />
                  <Box>
                    <Text fontWeight={600} fontSize="sm">
                      {platform.name}
                    </Text>
                    <Text fontSize="xs" color="ink.dim" noOfLines={1}>
                      {platform.typeLabel}
                    </Text>
                  </Box>
                </Flex>
              </Box>
            );
          })}
        </SimpleGrid>
        <Button variant="ghostNav" size="sm" mt={3} onClick={() => setSearch("")}>
          Toon alle {PLATFORM_CATALOG.length}+ platformen
        </Button>
      </MotionSection>

      {selectedPlatform && (
        <MotionSection>
          <Text fontSize="sm" fontWeight={600} letterSpacing="0.06em" color="ink.dim" mb={3}>
            Stap 2 · Hoe wilt u koppelen?
          </Text>
          <Text fontSize="xs" color="taupe.500" mb={4}>
            beschikbaarheid hangt af van gekozen platform
          </Text>
          <Grid templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }} gap={4}>
            {METHOD_CARDS.filter((m) => availableMethods.includes(m.method)).map((card) => {
              const active = selectedMethod === card.method;
              return (
                <Box
                  key={card.method}
                  as="button"
                  type="button"
                  textAlign="left"
                  p={5}
                  border="1px solid"
                  borderColor={active ? "azure.500" : "line.soft"}
                  borderRadius="base"
                  bg={active ? "azure.50" : "backgroundCard"}
                  transition="all 0.2s"
                  _hover={{ borderColor: "azure.400", boxShadow: "0 6px 20px rgba(26,58,92,0.06)" }}
                  onClick={() => setSelectedMethod(card.method)}
                >
                  <Text fontSize="2xl" mb={2}>
                    {card.icon}
                  </Text>
                  <Text fontSize="10px" letterSpacing="0.12em" textTransform="uppercase" color="ink.faint">
                    {card.label}
                  </Text>
                  <Text fontFamily="heading" fontSize="lg" mt={1} mb={2}>
                    {card.name}
                  </Text>
                  <Text fontSize="sm" color="ink.dim" lineHeight={1.6} mb={3}>
                    {card.desc}
                  </Text>
                  <Text fontSize="xs" color="taupe.500">
                    {card.platforms}
                  </Text>
                </Box>
              );
            })}
          </Grid>
        </MotionSection>
      )}

      <MotionSection>
        <FiscalDisclaimer>
          <strong>Welke methode is het beste?</strong> API-koppelingen zijn voorkeur (realtime). Geen API?
          CSV-upload. Banken/indexfondsen: jaaroverzicht. Edelmetaal of eigen wallet:{" "}
          <Link as={RouterLink} to="/portfolio/manual/transaction" color="azure.500">
            handmatige transactie
          </Link>
          .
        </FiscalDisclaimer>
      </MotionSection>

      {showBitvavoForm && (
        <MotionSection>
          <FiscalCard elevated p={6} borderLeft="3px solid" borderLeftColor="moss.500">
            <Text fontWeight={600} mb={4}>
              Bitvavo API-koppeling
            </Text>
            {error && <AuthAlert tone="error">{error}</AuthAlert>}
            {statusMessage && !error && <AuthAlert tone="info">{statusMessage}</AuthAlert>}
            <Box as="form" onSubmit={(e: React.FormEvent) => void handleBitvavoSubmit(e)}>
              <VStack align="stretch" spacing={4}>
                <AuthFormField
                  label="Label"
                  name="label"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                />
                <AuthFormField
                  label="API-key"
                  name="api_key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  isRequired
                  autoComplete="off"
                />
                <FormControl isRequired>
                  <FormLabel fontSize="sm" color="ink.dim">
                    API-secret
                  </FormLabel>
                  <Input
                    type="password"
                    value={apiSecret}
                    onChange={(e) => setApiSecret(e.target.value)}
                    autoComplete="off"
                    variant="fiscal"
                  />
                </FormControl>
                <Button
                  type="submit"
                  variant="fiscal"
                  isLoading={isSubmitting}
                  isDisabled={!user?.email_verified || !apiKey || !apiSecret}
                  alignSelf="flex-start"
                >
                  Bitvavo koppelen
                </Button>
              </VStack>
            </Box>
          </FiscalCard>
        </MotionSection>
      )}

      {selectedPlatform && selectedMethod === "csv" && selectedPlatform.id === "degiro" && (
        <MotionSection>
          <FiscalCard elevated p={6}>
            <Text fontWeight={600} mb={2}>
              DEGIRO · CSV-import
            </Text>
            <Text fontSize="sm" color="ink.dim" lineHeight={1.7} mb={4}>
              Upload uw DEGIRO-transactie-export op de pagina Mijn platformen. Duplicaten worden
              automatisch overgeslagen.
            </Text>
            <Button
              as={RouterLink}
              to="/platforms"
              state={{ focusDegiroCsv: true }}
              variant="fiscal"
              size="sm"
            >
              Naar DEGIRO CSV-upload
            </Button>
          </FiscalCard>
        </MotionSection>
      )}

      {selectedPlatform &&
        selectedMethod &&
        !showBitvavoForm &&
        !(selectedMethod === "csv" && selectedPlatform.id === "degiro") && (
        <MotionSection>
          <FiscalCard elevated p={6}>
            <Text fontWeight={600} mb={2}>
              {selectedPlatform.name} · catalogus
            </Text>
            <Text fontSize="sm" color="ink.dim" lineHeight={1.7} mb={4}>
              {selectedPlatform.description} De automatische koppeling voor dit platform volgt in
              een latere release. U kunt nu al:
            </Text>
            <Flex gap={2} flexWrap="wrap">
              {selectedMethod === "manual" || selectedPlatform.methods.includes("manual") ? (
                <Button as={RouterLink} to="/portfolio/manual/asset" variant="fiscal" size="sm">
                  Handmatig asset toevoegen
                </Button>
              ) : null}
              <Button
                as={RouterLink}
                to="/belasting/overig-vermogen"
                variant="fiscalOutline"
                size="sm"
              >
                Overig vermogen (bank/vastgoed)
              </Button>
              <Button as={RouterLink} to="/platforms/vergelijker" variant="ghostNav" size="sm">
                Andere platformen vergelijken
              </Button>
            </Flex>
          </FiscalCard>
        </MotionSection>
      )}
    </PageShell>
  );
}
