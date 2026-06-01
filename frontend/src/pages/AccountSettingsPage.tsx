import { useState } from "react";
import {
  Badge,
  Box,
  Button,
  Checkbox,
  Flex,
  Heading,
  Input,
  Link,
  Text,
  VStack,
} from "@chakra-ui/react";
import { useQueryClient } from "@tanstack/react-query";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import {
  deleteAccount,
  requestPasswordReset,
  resendVerificationEmail,
  updateProfile,
} from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { useUser } from "../contexts/UserContext";
import { getApiErrorMessage } from "../utils/apiError";

export default function AccountSettingsPage() {
  const { user, permissions, logout } = useUser();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [passwordResetMessage, setPasswordResetMessage] = useState("");
  const [verificationMessage, setVerificationMessage] = useState("");
  const [fiscalMessage, setFiscalMessage] = useState("");
  const [error, setError] = useState("");
  const [isSendingReset, setIsSendingReset] = useState(false);
  const [isSendingVerification, setIsSendingVerification] = useState(false);
  const [fiscalBusy, setFiscalBusy] = useState(false);
  const [deleteEmail, setDeleteEmail] = useState("");
  const [deleteBusy, setDeleteBusy] = useState(false);

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

  async function handleFiscalPartnerChange(checked: boolean) {
    setError("");
    setFiscalMessage("");
    setFiscalBusy(true);
    try {
      await updateProfile({ has_fiscal_partner: checked });
      await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      setFiscalMessage("Instelling opgeslagen. Herbereken uw belastingpositie indien nodig.");
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Instelling opslaan mislukt."));
    } finally {
      setFiscalBusy(false);
    }
  }

  async function handleDeleteAccount() {
    setError("");
    if (deleteEmail.trim().toLowerCase() !== userEmail.toLowerCase()) {
      setError("Vul uw e-mailadres exact in om te bevestigen.");
      return;
    }
    setDeleteBusy(true);
    try {
      await deleteAccount(userEmail);
      await logout();
      navigate("/auth/login", {
        replace: true,
        state: { message: "Uw account is verwijderd." },
      });
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Account verwijderen mislukt."));
    } finally {
      setDeleteBusy(false);
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
          <Text fontWeight={600}>Abonnement</Text>
          <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
            {permissions.isPremium
              ? "Werkelijk rendement, vergelijking met forfaitair en het volledige Box 3-rapport."
              : "Forfaitaire Box 3, peildatum, handmatige invoer en PDF-rapport. Upgrade voor werkelijk rendement."}
          </Text>
        </VStack>
      </FiscalCard>

      <FiscalCard p={6}>
        <VStack align="stretch" spacing={4}>
          <Text fontWeight={600}>Box 3 · Fiscaal partner</Text>
          <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
            Bij een fiscaal partner verdubbelt het heffingsvrije vermogen en de schuldendrempel
            in de forfaitaire berekening.
          </Text>
          <Checkbox
            isChecked={user.has_fiscal_partner}
            isDisabled={fiscalBusy}
            onChange={(e) => void handleFiscalPartnerChange(e.target.checked)}
          >
            Ik heb een fiscaal partner voor dit belastingjaar
          </Checkbox>
          {fiscalMessage && (
            <Text fontSize="sm" color="taupe.500">
              {fiscalMessage}
            </Text>
          )}
        </VStack>
      </FiscalCard>

      <FiscalCard p={6} borderColor="red.200">
        <VStack align="stretch" spacing={4}>
          <Text fontWeight={600}>Account verwijderen</Text>
          <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
            Uw account wordt gedeactiveerd en persoonsgegevens worden geanonimiseerd. U kunt
            daarna niet meer inloggen. Portefeuille- en belastingdata blijven bewaard volgens ons
            bewaarbeleid.
          </Text>
          <Box>
            <Text fontSize="xs" color="ink.dim" mb={1}>
              Typ {userEmail} ter bevestiging
            </Text>
            <Input
              size="sm"
              value={deleteEmail}
              onChange={(e) => setDeleteEmail(e.target.value)}
              placeholder={userEmail}
            />
          </Box>
          <Button
            variant="outline"
            colorScheme="red"
            alignSelf="flex-start"
            size="sm"
            isLoading={deleteBusy}
            onClick={() => void handleDeleteAccount()}
          >
            Account definitief verwijderen
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
