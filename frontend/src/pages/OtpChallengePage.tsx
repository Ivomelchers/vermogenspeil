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

import { completeMfaLogin } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { useUser } from "../contexts/UserContext";
import { getApiErrorMessage } from "../utils/apiError";

export default function OtpChallengePage() {
  const { completeMfaLoginFlow } = useUser();
  const navigate = useNavigate();

  const mfaToken = localStorage.getItem("mfa_token") ?? "";
  const rememberMe = localStorage.getItem("rememberMe") === "true";

  const [otp, setOtp] = useState("");
  const [backupCode, setBackupCode] = useState("");
  const [useBackupCode, setUseBackupCode] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!mfaToken) {
    return (
      <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
        <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
          <AuthAlert tone="error">
            Geen actieve MFA-sessie. Log opnieuw in.
          </AuthAlert>
          <Button as={RouterLink} to="/auth/login" variant="fiscal" w="full" mt={6}>
            Naar inloggen
          </Button>
        </FiscalCard>
      </Flex>
    );
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const tokens = await completeMfaLogin({
        mfa_token: mfaToken,
        otp: useBackupCode ? undefined : otp.trim(),
        backup_code: useBackupCode ? backupCode.trim() : undefined,
      });
      await completeMfaLoginFlow(tokens, rememberMe);
      navigate("/dashboard", { replace: true });
    } catch (submitError) {
      setError(
        getApiErrorMessage(
          submitError,
          "Verificatie mislukt. Controleer uw code en probeer opnieuw.",
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
            <Kicker mb={2}>Beveiliging</Kicker>
            <Heading size="lg">Tweefactorauthenticatie</Heading>
            <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
              {useBackupCode
                ? "Voer een ongebruikte backupcode in."
                : "Voer de 6-cijferige code uit uw authenticator-app in."}
            </Text>
          </Box>

          {error && <AuthAlert tone="error">{error}</AuthAlert>}

          {useBackupCode ? (
            <AuthFormField
              label="Backupcode"
              name="backup_code"
              type="text"
              autoComplete="one-time-code"
              value={backupCode}
              onChange={(event) => setBackupCode(event.target.value)}
              isRequired
            />
          ) : (
            <AuthFormField
              label="Verificatiecode"
              name="otp"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={otp}
              onChange={(event) => setOtp(event.target.value)}
              isRequired
            />
          )}

          <Button type="submit" variant="fiscal" w="full" isLoading={isSubmitting}>
            Verifiëren
          </Button>

          <Button
            type="button"
            variant="fiscalOutline"
            w="full"
            onClick={() => {
              setUseBackupCode((current) => !current);
              setError("");
            }}
          >
            {useBackupCode ? "Gebruik authenticator-code" : "Gebruik backupcode"}
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
