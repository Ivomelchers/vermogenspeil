import { useEffect } from "react";
import { Box, Button, Flex, Spinner, Text } from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { getAuthenticators } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";

export default function MfaSelectPage() {
  const navigate = useNavigate();
  const mfaToken = localStorage.getItem("mfa_token") ?? "";

  const authenticatorsQuery = useQuery({
    queryKey: ["mfa", "authenticators", mfaToken],
    queryFn: () => getAuthenticators(mfaToken),
    enabled: Boolean(mfaToken),
    retry: false,
  });

  useEffect(() => {
    if (!authenticatorsQuery.data) return;

    const otpAuthenticator = authenticatorsQuery.data.find(
      (authenticator) => authenticator.authenticator_type === "otp",
    );

    if (otpAuthenticator) {
      navigate("/auth/otp-challenge", { replace: true });
    } else {
      navigate("/auth/otp-enroll", { replace: true });
    }
  }, [authenticatorsQuery.data, navigate]);

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

  if (authenticatorsQuery.isLoading) {
    return (
      <Flex justify="center" align="center" minH="40vh">
        <Spinner color="azure.500" />
      </Flex>
    );
  }

  if (authenticatorsQuery.isError) {
    return (
      <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
        <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
          <AuthAlert tone="error">
            Authenticatiemethoden laden mislukt. Probeer opnieuw in te loggen.
          </AuthAlert>
          <Button as={RouterLink} to="/auth/login" variant="fiscalOutline" w="full" mt={6}>
            Naar inloggen
          </Button>
        </FiscalCard>
      </Flex>
    );
  }

  return (
    <Flex justify="center" align="center" minH="40vh">
      <Box textAlign="center">
        <Spinner color="azure.500" mb={4} />
        <Text color="ink.dim" fontSize="sm">
          MFA-sessie voorbereiden...
        </Text>
      </Box>
    </Flex>
  );
}
