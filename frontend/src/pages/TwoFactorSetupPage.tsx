import { useState } from "react";
import { Box, Button, Heading, Text, VStack } from "@chakra-ui/react";

import { resetMfa } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { getApiErrorMessage } from "../utils/apiError";

export default function TwoFactorSetupPage() {
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleResetMfa() {
    setError("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const response = await resetMfa();
      setSuccessMessage(
        response.message ??
          "Authenticator gereset. Stel 2FA opnieuw in bij de volgende login.",
      );
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Resetten van 2FA mislukt."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <VStack align="stretch" spacing={8} maxW="2xl">
      <Box>
        <Kicker mb={2}>Accountbeveiliging</Kicker>
        <Heading size="lg">Tweefactorauthenticatie</Heading>
        <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
          2FA wordt beheerd via Auth0. Bij login wordt u gevraagd een authenticator-app
          te gebruiken. Na reset moet u 2FA opnieuw instellen bij de volgende login.
        </Text>
      </Box>

      {error && <AuthAlert tone="error">{error}</AuthAlert>}
      {successMessage && <AuthAlert tone="success">{successMessage}</AuthAlert>}

      <FiscalCard p={6}>
        <Button
          variant="fiscalOutline"
          onClick={() => void handleResetMfa()}
          isLoading={isSubmitting}
        >
          Authenticator resetten
        </Button>
      </FiscalCard>
    </VStack>
  );
}
