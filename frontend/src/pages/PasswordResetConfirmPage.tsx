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
import { Link as RouterLink, useNavigate } from "react-router-dom";

import { confirmPasswordReset } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { getApiErrorMessage } from "../utils/apiError";

export default function PasswordResetConfirmPage() {
  const navigate = useNavigate();

  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");

    if (!token.trim()) {
      setError("Voer de resetcode in.");
      return;
    }

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

  return (
    <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
      <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
        <VStack as="form" align="stretch" spacing={6} onSubmit={handleSubmit}>
          <Box>
            <Kicker mb={2}>Account</Kicker>
            <Heading size="lg">Nieuw wachtwoord</Heading>
            <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
              Voer de resetcode in die u per e-mail ontvangt, en stel een nieuw wachtwoord in.
            </Text>
          </Box>

          {error && <AuthAlert tone="error">{error}</AuthAlert>}

          <AuthFormField
            label="Resetcode"
            name="token"
            type="text"
            placeholder="Plak hier uw resetcode"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            isRequired
          />

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

          <Text fontSize="sm" color="ink.dim" textAlign="center">
            <Link as={RouterLink} to="/auth/password/forgot" color="azure.500" fontWeight={500}>
              Nieuwe resetcode aanvragen
            </Link>
          </Text>
        </VStack>
      </FiscalCard>
    </Flex>
  );
}
