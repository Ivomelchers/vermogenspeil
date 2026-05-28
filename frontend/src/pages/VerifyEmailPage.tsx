import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Flex,
  Heading,
  Link,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useSearchParams } from "react-router-dom";

import { verifyEmail } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { getApiErrorMessage } from "../utils/apiError";

type VerifyState = "loading" | "success" | "error";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [state, setState] = useState<VerifyState>("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setState("error");
      setMessage("Geen verificatietoken gevonden in de link.");
      return;
    }

    verifyEmail(token)
      .then((response) => {
        setState("success");
        setMessage(response.message ?? "E-mailadres bevestigd.");
      })
      .catch((error) => {
        setState("error");
        setMessage(
          getApiErrorMessage(error, "Verificatie mislukt. Vraag een nieuwe link aan."),
        );
      });
  }, [token]);

  return (
    <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
      <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
        <VStack align="stretch" spacing={6}>
          <Box>
            <Kicker mb={2}>Account</Kicker>
            <Heading size="lg">E-mail bevestigen</Heading>
          </Box>

          {state === "loading" && (
            <Flex justify="center" py={8}>
              <Spinner color="azure.500" />
            </Flex>
          )}

          {state === "success" && <AuthAlert tone="success">{message}</AuthAlert>}
          {state === "error" && <AuthAlert tone="error">{message}</AuthAlert>}

          {state === "success" && (
            <Button
              as={RouterLink}
              to="/auth/login"
              state={{ message: "E-mailadres bevestigd. U kunt nu inloggen." }}
              variant="fiscal"
              w="full"
            >
              Naar inloggen
            </Button>
          )}

          {state === "error" && (
            <>
              <Button as={RouterLink} to="/auth/resend-verification" variant="fiscal" w="full">
                Nieuwe link aanvragen
              </Button>
              <Text fontSize="sm" color="ink.dim" textAlign="center">
                <Link as={RouterLink} to="/auth/register" color="azure.500" fontWeight={500}>
                  Terug naar registreren
                </Link>
              </Text>
            </>
          )}
        </VStack>
      </FiscalCard>
    </Flex>
  );
}
