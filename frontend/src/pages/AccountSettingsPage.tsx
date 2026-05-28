import { useState } from "react";
import {
  Badge,
  Box,
  Button,
  Flex,
  Heading,
  Link,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import { requestPasswordReset, resendVerificationEmail } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { useUser } from "../contexts/UserContext";
import { getApiErrorMessage } from "../utils/apiError";

export default function AccountSettingsPage() {
  const { user, permissions } = useUser();
  const [passwordResetMessage, setPasswordResetMessage] = useState("");
  const [verificationMessage, setVerificationMessage] = useState("");
  const [error, setError] = useState("");
  const [isSendingReset, setIsSendingReset] = useState(false);
  const [isSendingVerification, setIsSendingVerification] = useState(false);

  if (!user) {
    return null;
  }

  const userEmail = user.email;

  async function handlePasswordReset() {
    setError("");
    setPasswordResetMessage("");
    setIsSendingReset(true);

    try {
      const response = await requestPasswordReset(userEmail);
      setPasswordResetMessage(
        response.message ??
          "Als dit e-mailadres bij ons bekend is, ontvangt u een resetlink.",
      );
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Resetlink versturen mislukt."));
    } finally {
      setIsSendingReset(false);
    }
  }

  async function handleResendVerification() {
    setError("");
    setVerificationMessage("");
    setIsSendingVerification(true);

    try {
      const response = await resendVerificationEmail(userEmail);
      setVerificationMessage(
        response.message ??
          "Als dit e-mailadres bij ons bekend is, ontvangt u een nieuwe verificatielink.",
      );
    } catch {
      setVerificationMessage(
        "Als dit e-mailadres bij ons bekend is, ontvangt u een nieuwe verificatielink.",
      );
    } finally {
      setIsSendingVerification(false);
    }
  }

  return (
    <VStack align="stretch" spacing={8} maxW="2xl">
      <Box>
        <Kicker mb={2}>Account</Kicker>
        <Heading size="lg">Instellingen</Heading>
        <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
          Beheer uw profiel, wachtwoord en beveiliging.
        </Text>
      </Box>

      {error && <AuthAlert tone="error">{error}</AuthAlert>}

      <FiscalCard p={6}>
        <VStack align="stretch" spacing={4}>
          <Text fontWeight={600}>Profiel</Text>
          <Flex justify="space-between" gap={4} flexWrap="wrap">
            <Box>
              <Text fontSize="xs" color="ink.dim">
                Naam
              </Text>
              <Text>{user.full_name || user.first_name || "—"}</Text>
            </Box>
            <Box>
              <Text fontSize="xs" color="ink.dim">
                E-mailadres
              </Text>
              <Text>{user.email}</Text>
            </Box>
          </Flex>
          <Flex gap={2} flexWrap="wrap">
            <Badge colorScheme={permissions.isVerified ? "green" : "orange"}>
              {permissions.isVerified ? "E-mail bevestigd" : "E-mail niet bevestigd"}
            </Badge>
            <Badge colorScheme={permissions.isPremium ? "purple" : "gray"}>
              {permissions.isPremium ? "Premium" : "Gratis"}
            </Badge>
          </Flex>
          {!permissions.isVerified && (
            <>
              {verificationMessage && (
                <AuthAlert tone="info">{verificationMessage}</AuthAlert>
              )}
              <Button
                variant="fiscalOutline"
                alignSelf="flex-start"
                isLoading={isSendingVerification}
                onClick={() => void handleResendVerification()}
              >
                Verificatie-e-mail opnieuw versturen
              </Button>
            </>
          )}
        </VStack>
      </FiscalCard>

      <FiscalCard p={6}>
        <VStack align="stretch" spacing={4}>
          <Text fontWeight={600}>Wachtwoord</Text>
          <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
            U ontvangt per e-mail een link om een nieuw wachtwoord in te stellen. Uw
            tweefactorauthenticatie blijft actief.
          </Text>
          {passwordResetMessage && (
            <AuthAlert tone="success">{passwordResetMessage}</AuthAlert>
          )}
          <Button
            variant="fiscalOutline"
            alignSelf="flex-start"
            isLoading={isSendingReset}
            onClick={() => void handlePasswordReset()}
          >
            Wachtwoord resetlink versturen
          </Button>
        </VStack>
      </FiscalCard>

      <FiscalCard p={6}>
        <VStack align="stretch" spacing={4}>
          <Text fontWeight={600}>Beveiliging</Text>
          <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
            Stel tweefactorauthenticatie in of reset uw authenticator-app.
          </Text>
          <Link
            as={RouterLink}
            to="/settings/2fa"
            color="azure.500"
            fontWeight={500}
            fontSize="sm"
          >
            Naar 2FA-instellingen →
          </Link>
        </VStack>
      </FiscalCard>
    </VStack>
  );
}
