import { Box, Button, Flex, Heading, Link, Text, VStack } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";

export default function RegisterPage() {
  return (
    <Flex justify="center" align="center" minH={{ base: "auto", md: "50vh" }}>
      <FiscalCard p={{ base: 6, md: 10 }} w="full" maxW="md">
        <VStack align="stretch" spacing={6}>
          <Box>
            <Kicker mb={2}>Account</Kicker>
            <Heading size="lg">Registreren</Heading>
            <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.7}>
              Maak een account aan om uw vermogen te tracken en Box 3 voor te bereiden.
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
              Registratieformulier volgt in fase 2 (Auth &amp; Accounts).
            </Text>
          </Box>

          <Text fontSize="sm" color="ink.dim" textAlign="center">
            Al een account?{" "}
            <Link as={RouterLink} to="/login" color="azure.500" fontWeight={500}>
              Inloggen
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
