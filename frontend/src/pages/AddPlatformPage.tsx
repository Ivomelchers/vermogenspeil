import { useState } from "react";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Link,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { connectBitvavo, pollSyncJob } from "../api/integrations";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { useUser } from "../contexts/UserContext";
import { getApiErrorMessage } from "../utils/apiError";

export default function AddPlatformPage() {
  const navigate = useNavigate();
  const { user } = useUser();
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [label, setLabel] = useState("Bitvavo");
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
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
          setError(job.error_message || "Synchronisatie mislukt na koppeling.");
          return;
        }
      }

      navigate("/platforms", {
        state: { message: "Bitvavo succesvol gekoppeld en gesynchroniseerd." },
      });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Bitvavo koppelen mislukt."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <VStack align="stretch" spacing={8} maxW="2xl">
      <Box>
        <Kicker mb={2}>
          <Link as={RouterLink} to="/platforms" color="azure.500">
            ← Mijn platformen
          </Link>
        </Kicker>
        <Heading size="lg">Platform toevoegen</Heading>
        <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
          Koppel Bitvavo met een alleen-lezen API-key. Uw gegevens worden
          versleuteld opgeslagen en nooit in platte tekst bewaard.
        </Text>
      </Box>

      {user && !user.email_verified && (
        <AuthAlert tone="info">
          Bevestig eerst uw e-mailadres voordat u een platform kunt koppelen.
        </AuthAlert>
      )}

      {error && <AuthAlert tone="error">{error}</AuthAlert>}
      {statusMessage && !error && (
        <AuthAlert tone="info">{statusMessage}</AuthAlert>
      )}

      <FiscalCard
        p={6}
        borderLeft="3px solid"
        borderLeftColor="moss.500"
      >
        <Kicker mb={3} color="moss.500">
          API-koppeling · Bitvavo
        </Kicker>
        <Text fontSize="sm" color="ink.dim" mb={6} lineHeight={1.7}>
          Maak in Bitvavo een API-key aan met alleen{" "}
          <Box as="span" fontWeight={500} color="ink.primary">
            leesrechten
          </Box>
          . Geef geen handels- of opnamerechten.
        </Text>

        <Box
          as="form"
          onSubmit={(event: React.FormEvent) => void handleSubmit(event)}
        >
          <VStack align="stretch" spacing={4}>
            <AuthFormField
              label="Label (optioneel)"
              name="label"
              value={label}
              onChange={(event) => setLabel(event.target.value)}
              placeholder="Bitvavo"
            />
            <AuthFormField
              label="API-key"
              name="api_key"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              isRequired
              autoComplete="off"
            />
            <FormControl isRequired>
              <FormLabel fontSize="sm" color="ink.dim">
                API-secret
              </FormLabel>
              <Input
                type="password"
                name="api_secret"
                value={apiSecret}
                onChange={(event) => setApiSecret(event.target.value)}
                autoComplete="off"
                bg="paper"
                borderColor="line.DEFAULT"
                _focus={{
                  borderColor: "azure.500",
                  boxShadow: "0 0 0 1px var(--chakra-colors-azure-500)",
                }}
              />
            </FormControl>

            <Button
              type="submit"
              variant="fiscal"
              isLoading={isSubmitting}
              loadingText="Koppelen…"
              isDisabled={!user?.email_verified || !apiKey || !apiSecret}
              alignSelf="flex-start"
              mt={2}
            >
              Bitvavo koppelen
            </Button>
          </VStack>
        </Box>
      </FiscalCard>

      <FiscalCard p={5} bg="azure.50">
        <Text
          fontFamily="heading"
          fontStyle="italic"
          fontSize="sm"
          color="ink.primary"
          lineHeight={1.7}
        >
          Dit platform biedt fiscaal inzicht op basis van uw data — geen fiscaal
          advies. Controleer geïmporteerde posities altijd vóór uw aangifte.
        </Text>
      </FiscalCard>
    </VStack>
  );
}
