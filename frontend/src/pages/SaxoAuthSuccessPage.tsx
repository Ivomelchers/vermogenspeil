import { useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import PageShell from "../components/layout/PageShell";
import { Box, Text, Button, VStack } from "@chakra-ui/react";

export default function SaxoAuthSuccessPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const connectionId = searchParams.get("connection_id");

  useEffect(() => {
    // Auto-redirect to platforms after 2 seconds
    const timer = setTimeout(() => {
      navigate("/platforms", {
        state: { message: "Saxo Bank succesvol gekoppeld!" },
      });
    }, 2000);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <PageShell maxW="600px">
      <VStack spacing={6} align="center" justify="center" minH="60vh">
        <Box fontSize="5xl">✅</Box>
        <Text fontSize="2xl" fontWeight="bold">
          Saxo Bank gekoppeld!
        </Text>
        {connectionId && (
          <Text fontSize="sm" color="ink.dim">
            Connection ID: {connectionId}
          </Text>
        )}
        <Text color="ink.dim">U wordt doorgestuurd naar uw platformen...</Text>
        <Button onClick={() => navigate("/platforms")} variant="fiscal">
          Naar platformen
        </Button>
      </VStack>
    </PageShell>
  );
}
