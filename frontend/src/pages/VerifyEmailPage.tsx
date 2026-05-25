import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Flex,
  Heading,
  Spinner,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useSearchParams } from "react-router-dom";

import { verifyEmail } from "../api/auth";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";

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
          error.response?.data?.message ??
            "Verificatie mislukt. Vraag een nieuwe link aan.",
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

          {state !== "loading" && (
            <Text
              color={state === "success" ? "green.500" : "red.500"}
              fontSize="sm"
              lineHeight={1.7}
            >
              {message}
            </Text>
          )}

          <Button
            as={RouterLink}
            to={state === "success" ? "/login" : "/register"}
            variant="fiscal"
            w="full"
          >
            {state === "success" ? "Naar inloggen" : "Terug naar registreren"}
          </Button>
        </VStack>
      </FiscalCard>
    </Flex>
  );
}
