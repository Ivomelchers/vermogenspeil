import { type ReactNode } from "react";
import { Box, Flex, type FlexProps } from "@chakra-ui/react";

import Kicker from "./Kicker";

interface SectionHeaderProps extends Omit<FlexProps, "title"> {
  title: ReactNode;
  kicker?: string;
  action?: React.ReactNode;
}

/** Sectiekop zoals in MijnVermogen-Premium-v4 (serif-titel + kicker). */
export default function SectionHeader({
  title,
  kicker,
  action,
  ...props
}: SectionHeaderProps) {
  return (
    <Flex
      justify="space-between"
      align="flex-end"
      gap={4}
      flexWrap="wrap"
      mb={4}
      {...props}
    >
      <Box>
        <Box
          as="h2"
          fontFamily="heading"
          fontWeight={400}
          fontSize={{ base: "xl", md: "2xl" }}
          letterSpacing="-0.02em"
          color="ink.primary"
          lineHeight={1.2}
          sx={{
            em: { fontStyle: "italic", color: "azure.500" },
          }}
        >
          {title}
        </Box>
        {kicker && (
          <Kicker mt={2} letterSpacing="0.14em">
            {kicker}
          </Kicker>
        )}
      </Box>
      {action}
    </Flex>
  );
}
