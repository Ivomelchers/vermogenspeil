import { useSearchParams, useNavigate } from "react-router-dom";
import PageShell from "../components/layout/PageShell";
import { Box, Text, Button, VStack } from "@chakra-ui/react";
import AuthAlert from "../components/auth/AuthAlert";

export default function SaxoAuthErrorPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const error = searchParams.get("error");
  const description = searchParams.get("description");

  return (
    <PageShell maxW="600px">
      <VStack spacing={6} align="center" justify="center" minH="60vh">
        <Box fontSize="5xl">❌</Box>
        <Text fontSize="2xl" fontWeight="bold">
          Saxo verbinding mislukt
        </Text>
        <AuthAlert tone="error">
          {description || error || "Onbekende fout bij Saxo verbinding"}
        </AuthAlert>
        <VStack spacing={3} w="full">
          <Button
            onClick={() => navigate("/platforms?method=add&platform=saxo")}
            variant="fiscal"
            w="full"
          >
            Opnieuw proberen
          </Button>
          <Button onClick={() => navigate("/platforms")} variant="ghostNav" w="full">
            Terug naar platformen
          </Button>
        </VStack>
      </VStack>
    </PageShell>
  );
}
