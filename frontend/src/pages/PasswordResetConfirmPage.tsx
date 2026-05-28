import { FormEvent, useEffect, useState } from "react";
import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate, useSearchParams } from "react-router-dom";

import { confirmPasswordReset, validatePasswordResetToken } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import AuthLoading from "../components/common/AuthLoading";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { getApiErrorMessage } from "../utils/apiError";

export default function PasswordResetConfirmPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isValidating, setIsValidating] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!token) {
      setError("Ongeldige resetlink.");
      setIsValidating(false);
      return;
    }

    validatePasswordResetToken(token)
      .then((response) => {
        setEmail(response.data.email);
      })
      .catch((validateError) => {
        setError(
          getApiErrorMessage(
            validateError,
            "De resetlink is ongeldig of verlopen.",
          ),
        );
      })
      .finally(() => {
        setIsValidating(false);
      });
  }, [token]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Wachtwoorden komen niet overeen.");
      return;
    }

    setIsSubmitting(true);
    try {
      await confirmPasswordReset(token, password);
      navigate("/auth/login", {
        replace: true,
        state: { message: "Wachtwoord bijgewerkt. U kunt nu inloggen." },
      });
    } catch (submitError) {
      setError(
        getApiErrorMessage(
          submitError,
          "Wachtwoord resetten mislukt. Probeer het opnieuw.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isValidating) {
    return <AuthLoading />;
  }

  return (
    <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
      <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
        {error && !email ? (
          <VStack align="stretch" spacing={6}>
            <AuthAlert tone="error">{error}</AuthAlert>
            <Button as={RouterLink} to="/auth/password/forgot" variant="fiscalOutline" w="full">
              Nieuwe resetlink aanvragen
            </Button>
          </VStack>
        ) : (
          <VStack as="form" align="stretch" spacing={6} onSubmit={handleSubmit}>
            <Box>
              <Kicker mb={2}>Account</Kicker>
              <Heading size="lg">Nieuw wachtwoord</Heading>
              <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
                Stel een nieuw wachtwoord in voor {email}.
              </Text>
            </Box>

            {error && <AuthAlert tone="error">{error}</AuthAlert>}

            <AuthFormField
              label="Nieuw wachtwoord"
              name="password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              isRequired
            />

            <AuthFormField
              label="Bevestig wachtwoord"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              isRequired
            />

            <Button type="submit" variant="fiscal" w="full" isLoading={isSubmitting}>
              Wachtwoord opslaan
            </Button>
          </VStack>
        )}
      </FiscalCard>
    </Flex>
  );
}
