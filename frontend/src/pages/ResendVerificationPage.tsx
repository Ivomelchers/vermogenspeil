import { FormEvent, useState } from "react";
import {
  Box,
  Button,
  Flex,
  Heading,
  Link,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useLocation } from "react-router-dom";

import { resendVerificationEmail } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { getApiErrorMessage } from "../utils/apiError";

export default function ResendVerificationPage() {
  const location = useLocation();
  const initialEmail =
    (location.state as { email?: string } | null)?.email ?? "";

  const [email, setEmail] = useState(initialEmail);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const response = await resendVerificationEmail(email.trim());
      setSuccessMessage(
        response.message ??
          "Als dit e-mailadres bij ons bekend is, ontvangt u een nieuwe verificatielink.",
      );
    } catch (submitError) {
      setError(
        getApiErrorMessage(
          submitError,
          "Versturen mislukt. Probeer het later opnieuw.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
      <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
        <VStack as="form" align="stretch" spacing={6} onSubmit={handleSubmit}>
          <Box>
            <Kicker mb={2}>Account</Kicker>
            <Heading size="lg">Verificatie opnieuw</Heading>
            <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
              Vraag een nieuwe bevestigingslink aan voor uw e-mailadres.
            </Text>
          </Box>

          {successMessage && <AuthAlert tone="success">{successMessage}</AuthAlert>}
          {error && <AuthAlert tone="error">{error}</AuthAlert>}

          <AuthFormField
            label="E-mailadres"
            name="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            isRequired
          />

          <Button type="submit" variant="fiscal" w="full" isLoading={isSubmitting}>
            Verificatie-e-mail versturen
          </Button>

          <Text fontSize="sm" color="ink.dim" textAlign="center">
            <Link as={RouterLink} to="/auth/login" color="azure.500" fontWeight={500}>
              Terug naar inloggen
            </Link>
          </Text>
        </VStack>
      </FiscalCard>
    </Flex>
  );
}
