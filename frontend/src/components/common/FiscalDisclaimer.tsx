import { Box, Text } from "@chakra-ui/react";
import type { ReactNode } from "react";

interface FiscalDisclaimerProps {
  children: ReactNode;
}

/** cmp-disclaimer uit prototype */
export default function FiscalDisclaimer({ children }: FiscalDisclaimerProps) {
  return (
    <Box
      display="flex"
      gap={3}
      p={4}
      bg="azure.50"
      border="1px solid"
      borderColor="azure.200"
      borderRadius="sm"
      alignItems="flex-start"
    >
      <Text fontSize="lg" lineHeight={1} aria-hidden>
        ℹ
      </Text>
      <Text fontSize="sm" color="ink.primary" lineHeight={1.65}>
        {children}
      </Text>
    </Box>
  );
}
