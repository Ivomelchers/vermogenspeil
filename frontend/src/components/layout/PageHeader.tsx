import { type ReactNode } from "react";
import { Box, Flex, Text } from "@chakra-ui/react";

import Kicker from "../common/Kicker";

interface PageHeaderProps {
  kicker?: ReactNode;
  title: ReactNode;
  subtitle?: string;
  actions?: ReactNode;
  meta?: ReactNode;
}

/** Prototype page-header: kicker + serif titel met cursief accent + subtitle. */
export default function PageHeader({
  kicker,
  title,
  subtitle,
  actions,
  meta,
}: PageHeaderProps) {
  return (
    <Flex
      direction={{ base: "column", lg: "row" }}
      justify="space-between"
      align={{ base: "stretch", lg: "flex-end" }}
      gap={6}
      pb={2}
      borderBottom="1px solid"
      borderColor="line.soft"
    >
      <Box flex={1} minW={0}>
        {kicker && (
          <Kicker mb={3} letterSpacing="0.16em">
            {kicker}
          </Kicker>
        )}
        <Box
          as="h1"
          fontFamily="heading"
          fontWeight={400}
          fontSize={{ base: "2xl", md: "3xl" }}
          letterSpacing="-0.02em"
          lineHeight={1.15}
          color="ink.primary"
          sx={{
            em: { fontStyle: "italic", color: "azure.500" },
          }}
        >
          {title}
        </Box>
        {subtitle && (
          <Text color="ink.dim" fontSize="sm" mt={4} lineHeight={1.75} maxW="2xl">
            {subtitle}
          </Text>
        )}
        {meta && (
          <Text color="taupe.500" fontSize="xs" mt={3} lineHeight={1.6}>
            {meta}
          </Text>
        )}
      </Box>
      {actions && (
        <Flex gap={2} flexWrap="wrap" alignSelf={{ base: "flex-start", lg: "center" }}>
          {actions}
        </Flex>
      )}
    </Flex>
  );
}
