import { FormEvent, useState } from "react";
import {
  Badge,
  Box,
  Button,
  Heading,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { getMfaStatus, resetMfa, startMfaEnroll, type Auth0TokenResponse } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import MfaEnrollPanel from "../components/auth/MfaEnrollPanel";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { useUser } from "../contexts/UserContext";
import { getApiErrorMessage } from "../utils/apiError";

export default function TwoFactorSetupPage() {
  const { completeMfaLoginFlow } = useUser();
  const queryClient = useQueryClient();
  const rememberMe = localStorage.getItem("rememberMe") === "true";

  const [password, setPassword] = useState("");
  const [enrollToken, setEnrollToken] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");
  const [isStartingEnroll, setIsStartingEnroll] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const mfaStatusQuery = useQuery({
    queryKey: ["mfa", "status"],
    queryFn: getMfaStatus,
  });

  const enrolled = mfaStatusQuery.data?.enrolled ?? false;
  const statusAvailable = mfaStatusQuery.data?.status_available ?? true;

  async function handleStartEnroll(event: FormEvent) {
    event.preventDefault();
    setError("");
    setInfoMessage("");
    setIsStartingEnroll(true);

    try {
      const result = await startMfaEnroll(password);
      if (result.mfa_token) {
        setEnrollToken(result.mfa_token);
        return;
      }
      setInfoMessage(
        "Auth0 start geen 2FA-setup. Zet in Auth0 Dashboard → Security → Multi-factor Auth op 'Always' en probeer opnieuw.",
      );
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "2FA inschakelen mislukt."));
    } finally {
      setIsStartingEnroll(false);
    }
  }

  async function handleResetMfa() {
    setError("");
    setInfoMessage("");
    setIsResetting(true);

    try {
      const response = await resetMfa();
      setEnrollToken(null);
      setPassword("");
      await queryClient.invalidateQueries({ queryKey: ["mfa", "status"] });
      setInfoMessage(
        response.message ??
          "Authenticator gereset. Stel 2FA opnieuw in bij de volgende login.",
      );
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Resetten van 2FA mislukt."));
    } finally {
      setIsResetting(false);
    }
  }

  async function handleEnrollSuccess(tokens: Auth0TokenResponse) {
    await completeMfaLoginFlow(tokens, rememberMe);
    setEnrollToken(null);
    setPassword("");
    await queryClient.invalidateQueries({ queryKey: ["mfa", "status"] });
    setInfoMessage("2FA is geactiveerd op uw account.");
  }

  if (enrollToken) {
    return (
      <VStack align="stretch" spacing={8} maxW="2xl">
        <Box>
          <Kicker mb={2}>Accountbeveiliging</Kicker>
          <Heading size="lg">2FA instellen</Heading>
        </Box>
        <MfaEnrollPanel
          mfaToken={enrollToken}
          onSuccess={handleEnrollSuccess}
          onCancel={() => setEnrollToken(null)}
        />
      </VStack>
    );
  }

  return (
    <VStack align="stretch" spacing={8} maxW="2xl">
      <Box>
        <Kicker mb={2}>Accountbeveiliging</Kicker>
        <Heading size="lg">Tweefactorauthenticatie</Heading>
        <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
          Beveilig uw account met een authenticator-app. Bij login wordt een eenmalige
          verificatiecode gevraagd.
        </Text>
      </Box>

      {error && <AuthAlert tone="error">{error}</AuthAlert>}
      {infoMessage && <AuthAlert tone="success">{infoMessage}</AuthAlert>}
      {!statusAvailable && !mfaStatusQuery.isLoading && (
        <AuthAlert tone="info">
          MFA-status kon niet worden opgehaald. Voeg in Auth0 bij de M2M-app de scope{" "}
          <strong>read:authentication_methods</strong> toe (naast delete/create/update).
        </AuthAlert>
      )}

      <FiscalCard p={6}>
        <VStack align="stretch" spacing={4}>
          <Text fontWeight={600}>Status</Text>
          {mfaStatusQuery.isLoading ? (
            <Text color="ink.dim" fontSize="sm">
              Status laden...
            </Text>
          ) : (
            <Badge alignSelf="flex-start" colorScheme={enrolled ? "green" : "orange"}>
              {enrolled ? "2FA actief" : "2FA niet ingesteld"}
            </Badge>
          )}
        </VStack>
      </FiscalCard>

      {!enrolled && !mfaStatusQuery.isLoading && (
        <FiscalCard p={6}>
          <VStack
            as="form"
            align="stretch"
            spacing={4}
            onSubmit={handleStartEnroll}
          >
            <Text fontWeight={600}>2FA inschakelen</Text>
            <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
              Bevestig uw wachtwoord om de setup te starten. Scan daarna de QR-code
              met uw authenticator-app.
            </Text>
            <AuthFormField
              label="Huidig wachtwoord"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              isRequired
            />
            <Button
              type="submit"
              variant="fiscal"
              alignSelf="flex-start"
              isLoading={isStartingEnroll}
            >
              2FA instellen
            </Button>
          </VStack>
        </FiscalCard>
      )}

      {enrolled && (
        <FiscalCard p={6}>
          <VStack align="stretch" spacing={4}>
            <Text fontWeight={600}>Authenticator resetten</Text>
            <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
              Verwijdert uw huidige authenticator. Bij de volgende login moet u 2FA
              opnieuw instellen.
            </Text>
            <Button
              variant="fiscalOutline"
              alignSelf="flex-start"
              isLoading={isResetting}
              onClick={() => void handleResetMfa()}
            >
              Authenticator resetten
            </Button>
          </VStack>
        </FiscalCard>
      )}
    </VStack>
  );
}
