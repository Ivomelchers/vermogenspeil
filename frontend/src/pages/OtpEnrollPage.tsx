import { FormEvent, useEffect, useState } from "react";
import {
  Box,
  Button,
  Code,
  Flex,
  Heading,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import {
  enrollAuthenticator,
  enrollAuthenticatorConfirm,
} from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { useUser } from "../contexts/UserContext";
import { getApiErrorMessage } from "../utils/apiError";

export default function OtpEnrollPage() {
  const { completeMfaLoginFlow } = useUser();
  const navigate = useNavigate();
  const mfaToken = localStorage.getItem("mfa_token") ?? "";
  const rememberMe = localStorage.getItem("rememberMe") === "true";

  const [enrollData, setEnrollData] = useState<{
    secret: string;
    barcode_uri: string;
    client_secret?: string;
  } | null>(null);
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!mfaToken) {
      setIsLoading(false);
      return;
    }

    enrollAuthenticator(mfaToken)
      .then((data) => setEnrollData(data))
      .catch(() => setError("2FA-setup starten mislukt."))
      .finally(() => setIsLoading(false));
  }, [mfaToken]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!enrollData?.client_secret) return;

    setError("");
    setIsSubmitting(true);

    try {
      const tokens = await enrollAuthenticatorConfirm({
        mfa_token: mfaToken,
        otp: otp.trim(),
        client_secret: enrollData.client_secret,
      });
      await completeMfaLoginFlow(tokens, rememberMe);
      navigate("/react/dashboard", { replace: true });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Ongeldige verificatiecode."));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!mfaToken) {
    return (
      <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
        <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
          <AuthAlert tone="error">Geen actieve MFA-sessie. Log opnieuw in.</AuthAlert>
          <Button as={RouterLink} to="/auth/login" variant="fiscal" w="full" mt={6}>
            Naar inloggen
          </Button>
        </FiscalCard>
      </Flex>
    );
  }

  if (isLoading) {
    return (
      <Flex justify="center" align="center" minH="40vh">
        <Spinner color="azure.500" />
      </Flex>
    );
  }

  return (
    <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
      <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
        <VStack as="form" align="stretch" spacing={6} onSubmit={handleSubmit}>
          <Box>
            <Kicker mb={2}>Beveiliging</Kicker>
            <Heading size="lg">2FA instellen</Heading>
            <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
              Scan de QR-code of voer de geheime sleutel handmatig in uw authenticator-app in.
            </Text>
          </Box>

          {error && <AuthAlert tone="error">{error}</AuthAlert>}

          {enrollData && (
            <>
              <Code p={3} whiteSpace="pre-wrap">
                {enrollData.secret}
              </Code>
              <Text fontSize="xs" color="ink.dim" wordBreak="break-all">
                {enrollData.barcode_uri}
              </Text>
            </>
          )}

          <AuthFormField
            label="Verificatiecode"
            name="otp"
            type="text"
            inputMode="numeric"
            value={otp}
            onChange={(event) => setOtp(event.target.value)}
            isRequired
          />

          <Button type="submit" variant="fiscal" w="full" isLoading={isSubmitting}>
            2FA activeren
          </Button>
        </VStack>
      </FiscalCard>
    </Flex>
  );
}
