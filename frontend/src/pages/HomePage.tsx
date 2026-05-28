import { Box, Button, Grid, Heading, Text, VStack } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import MoneyText from "../components/common/MoneyText";
import { useUser } from "../contexts/UserContext";

export default function HomePage() {
  const { isAuthenticated } = useUser();

  return (
    <Grid templateColumns={{ base: "1fr", lg: "1.3fr 1fr" }} gap={12} alignItems="center">
      <VStack align="start" spacing={6}>
        <Kicker>MijnVermogen · Fiscaal instrument</Kicker>
        <Heading as="h1" size="2xl" maxW="2xl" lineHeight={1.15} letterSpacing="-0.02em">
          Uw vermogen, helder en fiscaal correct
        </Heading>
        <Text color="ink.dim" fontSize="lg" maxW="xl" lineHeight={1.7}>
          Track al uw beleggingen op één plek en bereid uw Box 3-aangifte voor
          met vertrouwen. Geen crypto-app — een serieus instrument voor serieus
          geld.
        </Text>
        <Box pt={2}>
          {isAuthenticated ? (
            <Button as={RouterLink} to="/dashboard" variant="fiscal">
              Naar dashboard
            </Button>
          ) : (
            <>
              <Button as={RouterLink} to="/auth/register" variant="fiscal" mr={3}>
                Account aanmaken
              </Button>
              <Button as={RouterLink} to="/auth/login" variant="fiscalOutline">
                Inloggen
              </Button>
            </>
          )}
        </Box>
      </VStack>

      <FiscalCard p={8}>
        <Kicker mb={4}>Belastingjaar 2026 · Forfaitair stelsel</Kicker>
        <Text fontFamily="heading" fontStyle="italic" fontSize="15px" color="ink.dim" mb={2}>
          Te betalen belasting
        </Text>
        <MoneyText variant="display" fontSize={{ base: "48px", md: "64px" }}>
          €174
        </MoneyText>
        <Text color="ink.dim" fontSize="sm" mt={4} lineHeight={1.7}>
          Berekend over uw vermogen van € 64.820 op peildatum 1 januari 2026.
          Aanslag ontvangt u in 2027.
        </Text>
      </FiscalCard>
    </Grid>
  );
}
