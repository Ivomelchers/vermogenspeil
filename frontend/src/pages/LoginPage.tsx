import { Box, Button, Flex, Heading, Link, Text, VStack } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";

export default function LoginPage() {
  return (
    <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
      <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
        <VStack align="stretch" spacing={6}>
          <Box>
            <Kicker mb={2}>Account</Kicker>
            <Heading size="lg">Inloggen</Heading>
            <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
              Toegang tot uw vermogensoverzicht en Box 3-berekening.
            </Text>
          </Box>

          <Box
            py={8}
            px={4}
            border="1px dashed"
            borderColor="line.soft"
            borderRadius="base"
            textAlign="center"
          >
            <Text color="ink.faint" fontSize="sm">
              Loginformulier volgt in fase 2 (Auth &amp; Accounts).
            </Text>
          </Box>

          <Text fontSize="sm" color="ink.dim" textAlign="center">
            Nog geen account?{" "}
            <Link as={RouterLink} to="/register" color="azure.500" fontWeight={500}>
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
