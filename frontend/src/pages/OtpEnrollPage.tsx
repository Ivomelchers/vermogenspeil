import { Box, Button, Flex, Heading, VStack } from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";

import AuthAlert from "../components/auth/AuthAlert";
import MfaEnrollPanel from "../components/auth/MfaEnrollPanel";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { useUser } from "../contexts/UserContext";

export default function OtpEnrollPage() {
  const { completeMfaLoginFlow } = useUser();
  const navigate = useNavigate();
  const mfaToken = localStorage.getItem("mfa_token") ?? "";
  const rememberMe = localStorage.getItem("rememberMe") === "true";

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

  return (
    <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
      <Box w="full" maxW="md">
        <VStack align="stretch" spacing={6}>
          <Box>
            <Kicker mb={2}>Beveiliging</Kicker>
            <Heading size="lg">2FA instellen</Heading>
          </Box>
          <MfaEnrollPanel
            mfaToken={mfaToken}
            onSuccess={async (tokens) => {
              await completeMfaLoginFlow(tokens, rememberMe);
              navigate("/dashboard", { replace: true });
            }}
          />
        </VStack>
      </Box>
    </Flex>
  );
}
