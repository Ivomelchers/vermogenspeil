import { FormEvent, useState } from "react";
import {
  Box,
  Button,
  Checkbox,
  Flex,
  Heading,
  Link,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import { register } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { getApiErrorMessage } from "../utils/apiError";

export default function RegisterPage() {
  const [firstName, setFirstName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const response = await register({
        email: email.trim(),
        password,
        first_name: firstName.trim(),
        terms_accepted: termsAccepted,
      });

      setSuccessMessage(
        response.message ??
          "Registratie gelukt. Bevestig uw e-mailadres via de link in uw inbox.",
      );
      setPassword("");
      setTermsAccepted(false);
    } catch (submitError) {
      setError(
        getApiErrorMessage(submitError, "Registratie mislukt. Probeer het opnieuw."),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
      <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
        {successMessage ? (
          <VStack align="stretch" spacing={6}>
            <Box>
              <Kicker mb={2}>Account</Kicker>
              <Heading size="lg">Controleer uw inbox</Heading>
            </Box>

            <AuthAlert tone="success">{successMessage}</AuthAlert>

            <Text color="ink.dim" fontSize="sm" lineHeight={1.7}>
              We hebben een bevestigingslink gestuurd naar{" "}
              <Box as="span" fontWeight={500} color="ink.primary">
                {email}
              </Box>
              . Na bevestiging kunt u inloggen.
            </Text>

            <Button as={RouterLink} to="/auth/login" variant="fiscal" w="full">
              Naar inloggen
            </Button>

            <Button
              as={RouterLink}
              to="/auth/resend-verification"
              state={{ email }}
              variant="fiscalOutline"
              w="full"
            >
              Geen e-mail ontvangen?
            </Button>
          </VStack>
        ) : (
          <VStack as="form" align="stretch" spacing={6} onSubmit={handleSubmit}>
            <Box>
              <Kicker mb={2}>Account</Kicker>
              <Heading size="lg">Registreren</Heading>
              <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
                Maak een account aan om uw vermogen te tracken en Box 3 voor te bereiden.
              </Text>
            </Box>

            {error && <AuthAlert tone="error">{error}</AuthAlert>}

            <AuthFormField
              label="Voornaam"
              name="first_name"
              autoComplete="given-name"
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
              isRequired
            />

            <AuthFormField
              label="E-mailadres"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              isRequired
            />

            <AuthFormField
              label="Wachtwoord"
              name="password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              helperText="Minimaal 12 tekens."
              isRequired
              minLength={12}
            />

            <Checkbox
              isChecked={termsAccepted}
              onChange={(event) => setTermsAccepted(event.target.checked)}
              alignItems="flex-start"
              sx={{
                ".chakra-checkbox__control": {
                  borderColor: "line.DEFAULT",
                  _checked: { bg: "azure.500", borderColor: "azure.500" },
                },
              }}
            >
              <Text fontSize="sm" color="ink.dim" lineHeight={1.6}>
                Ik ga akkoord met de algemene voorwaarden en privacyverklaring.
              </Text>
            </Checkbox>

            <Button
              type="submit"
              variant="fiscal"
              w="full"
              isLoading={isSubmitting}
              isDisabled={!termsAccepted}
            >
              Account aanmaken
            </Button>

            <Text fontSize="sm" color="ink.dim" textAlign="center">
              Al een account?{" "}
              <Link as={RouterLink} to="/auth/login" color="azure.500" fontWeight={500}>
                Inloggen
              </Link>
            </Text>

            <Button as={RouterLink} to="/" variant="fiscalOutline" w="full">
              Terug naar home
            </Button>
          </VStack>
        )}
      </FiscalCard>
    </Flex>
  );
}
