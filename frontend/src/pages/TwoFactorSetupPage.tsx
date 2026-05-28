import { FormEvent, useState } from "react";
import {
  Badge,
  Box,
  Button,
  Code,
  Heading,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getMfaStatus,
  resetMfa,
  startTwoFactorSetup,
  disableTwoFactor,
  type TwoFactorSetupResponse,
} from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import MfaEnrollPanel from "../components/auth/MfaEnrollPanel";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { getApiErrorMessage } from "../utils/apiError";

export default function TwoFactorSetupPage() {
  const queryClient = useQueryClient();

  const [setupData, setSetupData] = useState<TwoFactorSetupResponse | null>(null);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [disablePassword, setDisablePassword] = useState("");
  const [disableOtp, setDisableOtp] = useState("");
  const [error, setError] = useState("");
  const [infoMessage, setInfoMessage] = useState("");
  const [isStartingEnroll, setIsStartingEnroll] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isDisabling, setIsDisabling] = useState(false);

  const mfaStatusQuery = useQuery({
    queryKey: ["mfa", "status"],
    queryFn: getMfaStatus,
  });

  const enrolled = mfaStatusQuery.data?.enrolled ?? false;

  async function handleStartEnroll() {
    setError("");
    setInfoMessage("");
    setIsStartingEnroll(true);

    try {
      const result = await startTwoFactorSetup();
      setSetupData(result);
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
      setSetupData(null);
      setBackupCodes([]);
      await queryClient.invalidateQueries({ queryKey: ["mfa", "status"] });
      setInfoMessage(response.message ?? "Authenticator gereset. Stel 2FA opnieuw in.");
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Resetten van 2FA mislukt."));
    } finally {
      setIsResetting(false);
    }
  }

  async function handleEnrollSuccess(codes: string[]) {
    setSetupData(null);
    setBackupCodes(codes);
    await queryClient.invalidateQueries({ queryKey: ["mfa", "status"] });
    setInfoMessage("2FA is geactiveerd op uw account.");
  }

  async function handleDisable(event: FormEvent) {
    event.preventDefault();
    setError("");
    setInfoMessage("");
    setIsDisabling(true);

    try {
      const response = await disableTwoFactor(disablePassword, disableOtp.trim());
      setDisablePassword("");
      setDisableOtp("");
      await queryClient.invalidateQueries({ queryKey: ["mfa", "status"] });
      setInfoMessage(response.message ?? "2FA is uitgeschakeld.");
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "2FA uitschakelen mislukt."));
    } finally {
      setIsDisabling(false);
    }
  }

  if (setupData) {
    return (
      <VStack align="stretch" spacing={8} maxW="2xl">
        <Box>
          <Kicker mb={2}>Accountbeveiliging</Kicker>
          <Heading size="lg">2FA instellen</Heading>
        </Box>
        <MfaEnrollPanel
          setupData={setupData}
          onSuccess={handleEnrollSuccess}
          onCancel={() => setSetupData(null)}
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

      {backupCodes.length > 0 && (
        <FiscalCard p={6}>
          <VStack align="stretch" spacing={3}>
            <Text fontWeight={600}>Backupcodes</Text>
            <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
              Bewaar deze codes op een veilige plek. Elke code kan één keer worden gebruikt
              als uw authenticator niet beschikbaar is.
            </Text>
            {backupCodes.map((code) => (
              <Code key={code} p={2}>
                {code}
              </Code>
            ))}
          </VStack>
        </FiscalCard>
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
          <VStack align="stretch" spacing={4}>
            <Text fontWeight={600}>2FA inschakelen</Text>
            <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
              Scan daarna de QR-code met uw authenticator-app en bevestig met een code.
            </Text>
            <Button
              variant="fiscal"
              alignSelf="flex-start"
              isLoading={isStartingEnroll}
              onClick={() => void handleStartEnroll()}
            >
              2FA instellen
            </Button>
          </VStack>
        </FiscalCard>
      )}

      {enrolled && (
        <>
          <FiscalCard p={6}>
            <VStack
              as="form"
              align="stretch"
              spacing={4}
              onSubmit={handleDisable}
            >
              <Text fontWeight={600}>2FA uitschakelen</Text>
              <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
                Bevestig met uw wachtwoord en een actuele verificatiecode.
              </Text>
              <AuthFormField
                label="Huidig wachtwoord"
                name="password"
                type="password"
                autoComplete="current-password"
                value={disablePassword}
                onChange={(event) => setDisablePassword(event.target.value)}
                isRequired
              />
              <AuthFormField
                label="Verificatiecode"
                name="otp"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={disableOtp}
                onChange={(event) => setDisableOtp(event.target.value)}
                isRequired
              />
              <Button
                type="submit"
                variant="fiscalOutline"
                alignSelf="flex-start"
                isLoading={isDisabling}
              >
                2FA uitschakelen
              </Button>
            </VStack>
          </FiscalCard>

          <FiscalCard p={6}>
            <VStack align="stretch" spacing={4}>
              <Text fontWeight={600}>Authenticator resetten</Text>
              <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
                Verwijdert uw huidige authenticator zodat u 2FA opnieuw kunt instellen.
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
        </>
      )}
    </VStack>
  );
}
