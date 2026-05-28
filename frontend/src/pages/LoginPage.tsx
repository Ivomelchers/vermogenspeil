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
import { Link as RouterLink, useLocation, useNavigate } from "react-router-dom";

import { resendVerificationEmail } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { useUser } from "../contexts/UserContext";
import { getApiErrorCode, getApiErrorMessage } from "../utils/apiError";

export default function LoginPage() {
  const { loginWithUsernameAndPassword, isLoggingIn } = useUser();
  const navigate = useNavigate();
  const location = useLocation();
  const locationState = (location.state as { from?: string; message?: string } | null) ?? {};
  const redirectMessage = locationState.message;
  const redirectTo = locationState.from ?? "/react/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [errorCode, setErrorCode] = useState<string | undefined>();
  const [resendState, setResendState] = useState<"idle" | "loading" | "sent">("idle");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setErrorCode(undefined);

    try {
      const result = await loginWithUsernameAndPassword(email.trim(), password, rememberMe);
      localStorage.setItem("rememberMe", rememberMe ? "true" : "false");

      if (result.status === "mfa_required" || result.status === "enrollment_required") {
        navigate("/auth/mfa-select", { replace: true });
        return;
      }

      navigate(redirectTo, { replace: true });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Inloggen mislukt. Probeer het opnieuw."));
      setErrorCode(getApiErrorCode(submitError));
    }
  }

  async function handleResendVerification() {
    if (!email.trim()) {
      setError("Vul uw e-mailadres in om een nieuwe verificatielink te ontvangen.");
      return;
    }

    setResendState("loading");
    try {
      await resendVerificationEmail(email.trim());
      setResendState("sent");
    } catch {
      setResendState("sent");
    }
  }

  return (
    <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
      <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
        <VStack as="form" align="stretch" spacing={6} onSubmit={handleSubmit}>
          <Box>
            <Kicker mb={2}>Account</Kicker>
            <Heading size="lg">Inloggen</Heading>
            <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
              Toegang tot uw vermogensoverzicht en Box 3-berekening.
            </Text>
          </Box>

          {redirectMessage && <AuthAlert tone="success">{redirectMessage}</AuthAlert>}
          {error && <AuthAlert tone="error">{error}</AuthAlert>}

          {errorCode === "email_not_verified" &&
            (resendState === "sent" ? (
              <AuthAlert tone="info">
                Als dit e-mailadres bij ons bekend is, ontvangt u een nieuwe verificatielink.
              </AuthAlert>
            ) : (
              <Button
                type="button"
                variant="fiscalOutline"
                w="full"
                isLoading={resendState === "loading"}
                onClick={handleResendVerification}
              >
                Verificatie-e-mail opnieuw versturen
              </Button>
            ))}

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
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            isRequired
          />

          <Text fontSize="sm" textAlign="right">
            <Link as={RouterLink} to="/auth/password/forgot" color="azure.500" fontWeight={500}>
              Wachtwoord vergeten?
            </Link>
          </Text>

          <Checkbox
            isChecked={rememberMe}
            onChange={(event) => setRememberMe(event.target.checked)}
            alignItems="flex-start"
            sx={{
              ".chakra-checkbox__control": {
                borderColor: "line.DEFAULT",
                _checked: { bg: "azure.500", borderColor: "azure.500" },
              },
            }}
          >
            <Text fontSize="sm" color="ink.dim" lineHeight={1.6}>
              Onthoud mij op dit apparaat
            </Text>
          </Checkbox>

          <Button type="submit" variant="fiscal" w="full" isLoading={isLoggingIn}>
            Inloggen
          </Button>

          <Text fontSize="sm" color="ink.dim" textAlign="center">
            Nog geen account?{" "}
            <Link as={RouterLink} to="/auth/register" color="azure.500" fontWeight={500}>
              Registreren
            </Link>
          </Text>

          <Button as={RouterLink} to="/" variant="fiscalOutline" w="full">
            Terug naar home
          </Button>
        </VStack>
      </FiscalCard>
    </Flex>
  );
}
