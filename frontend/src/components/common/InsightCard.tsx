import { type ReactNode } from "react";
import { Box, Text } from "@chakra-ui/react";

import Kicker from "./Kicker";
import MoneyText, { type MoneyTone } from "./MoneyText";

interface InsightCardProps {
  label: string;
  value: ReactNode;
  delta?: string;
  tone?: MoneyTone;
  accent?: "ochre" | "default";
}

export default function InsightCard({
  label,
  value,
  delta,
  tone = "default",
  accent = "default",
}: InsightCardProps) {
  return (
    <Box
      bg="backgroundCard"
      border="1px solid"
      borderColor="line.DEFAULT"
      borderRadius="base"
      p={5}
      transition="border-color 0.15s ease, box-shadow 0.15s ease"
      _hover={{
        borderColor: "taupe.500",
        boxShadow: "md",
      }}
    >
      <Kicker mb={3}>{label}</Kicker>
      {typeof value === "string" ? (
        <MoneyText
          variant="display"
          fontSize={{ base: "28px", md: "32px" }}
          tone={tone}
          color={accent === "ochre" ? "azure.500" : undefined}
          letterSpacing="-0.02em"
        >
          {value}
        </MoneyText>
      ) : (
        <Box fontFamily="heading" fontSize={{ base: "28px", md: "32px" }} letterSpacing="-0.02em">
          {value}
        </Box>
      )}
      {delta && (
        <Text
          fontSize="xs"
          mt={2}
          color={tone === "positive" ? "moss.500" : tone === "negative" ? "rust.500" : "ink.dim"}
          fontStyle="italic"
          fontFamily="heading"
        >
          {delta}
        </Text>
      )}
    </Box>
  );
}
