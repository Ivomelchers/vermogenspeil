import { Box, Grid, Text, VStack } from "@chakra-ui/react";

import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import MoneyText from "../components/common/MoneyText";

export default function DashboardPage() {
  return (
    <VStack align="stretch" spacing={8}>
      <Grid
        templateColumns={{ base: "1fr", xl: "1.3fr 1fr" }}
        gap={12}
        pb={8}
        borderBottom="1px solid"
        borderColor="line.DEFAULT"
      >
        <Box>
          <Kicker mb={4}>
            Overzicht · <Box as="span" color="taupe.500">25 mei 2026</Box>
          </Kicker>
          <Text
            fontFamily="heading"
            fontStyle="italic"
            fontSize="15px"
            color="ink.dim"
            mb={1.5}
          >
            Totaal vermogen
          </Text>
          <MoneyText variant="display" mb={5}>
            <Box as="span" fontSize={{ base: "28px", md: "32px" }} color="ink.dim" fontStyle="italic" fontWeight={300}>
              €
            </Box>{" "}
            64.820
            <Box as="span" fontSize={{ base: "28px", md: "36px" }} color="ink.dim" fontWeight={300}>
              ,00
            </Box>
          </MoneyText>
          <Box display="flex" gap={6} flexWrap="wrap">
            <MoneyText variant="delta" tone="positive">
              + € 2.341,80
            </MoneyText>
            <Kicker>YTD rendement</Kicker>
          </Box>
        </Box>

        <FiscalCard p={6}>
          <Kicker mb={3}>Belastingjaar 2026 · Peildatum 1 jan</Kicker>
          <Text fontFamily="heading" fontStyle="italic" fontSize="15px" color="ink.dim" mb={2}>
            Te betalen belasting
          </Text>
          <MoneyText variant="display" fontSize={{ base: "48px", md: "56px" }}>
            €174
          </MoneyText>
          <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.6}>
            Berekend over uw vermogen van € 64.820. Volledige Box 3-berekening
            volgt in fase 6.
          </Text>
        </FiscalCard>
      </Grid>

      <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", xl: "repeat(4, 1fr)" }} gap={4}>
        <InsightCard label="Beleggingen" value="€ 48.200" delta="+ 4,2%" tone="positive" />
        <InsightCard label="Crypto" value="€ 9.420" delta="− 1,1%" tone="negative" />
        <InsightCard label="Sparen" value="€ 7.200" delta="+ 0,3%" tone="positive" />
        <InsightCard label="Box 3 grondslag" value="€ 64.820" delta="Peildatum" tone="accent" />
      </Grid>
    </VStack>
  );
}

function InsightCard({
  label,
  value,
  delta,
  tone,
}: {
  label: string;
  value: string;
  delta: string;
  tone: "positive" | "negative" | "accent";
}) {
  const valueTone = tone === "positive" ? "positive" : tone === "negative" ? "negative" : "default";
  const deltaTone = tone === "accent" ? "default" : valueTone;

  return (
    <FiscalCard p={5}>
      <Kicker mb={3}>{label}</Kicker>
      <MoneyText
        fontFamily="heading"
        fontSize="32px"
        letterSpacing="-0.02em"
        tone={valueTone === "default" ? "accent" : valueTone}
        mb={2}
      >
        {value}
      </MoneyText>
      <MoneyText variant="delta" tone={deltaTone} color={deltaTone === "default" ? "ink.dim" : undefined}>
        {delta}
      </MoneyText>
    </FiscalCard>
  );
}
