import { Box, Button, Text, VStack } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import { useUser } from "../../contexts/UserContext";
import FiscalCard from "./FiscalCard";
import Kicker from "./Kicker";

interface PremiumGateProps {
  title?: string;
  description?: string;
  children?: React.ReactNode;
  compact?: boolean;
}

export default function PremiumGate({
  title = "Premium",
  description = "Werkelijk rendement, vergelijking met forfaitair en het volledige Box 3-rapport zijn beschikbaar met Premium.",
  children,
  compact = false,
}: PremiumGateProps) {
  const { permissions } = useUser();

  if (permissions.isPremium) {
    return <>{children}</>;
  }

  if (compact) {
    return (
      <FiscalCard p={4} borderColor="azure.300" bg="azure.50">
        <Kicker mb={2} color="azure.500">
          {title}
        </Kicker>
        <Text fontSize="sm" color="ink.dim" lineHeight={1.7} mb={3}>
          {description}
        </Text>
        <Button as={RouterLink} to="/settings/account" variant="fiscalOutline" size="sm">
          Meer over Premium
        </Button>
      </FiscalCard>
    );
  }

  return (
    <Box position="relative">
      {children && (
        <Box opacity={0.35} pointerEvents="none" userSelect="none" aria-hidden>
          {children}
        </Box>
      )}
      <Box
        position={children ? "absolute" : "relative"}
        inset={children ? 0 : undefined}
        display="flex"
        alignItems="center"
        justifyContent="center"
        p={6}
        borderRadius="base"
        bg={children ? "rgba(250, 248, 245, 0.92)" : undefined}
      >
        <VStack spacing={3} maxW="360px" textAlign="center">
          <Box
            w="36px"
            h="36px"
            bg="azure.500"
            borderRadius="full"
            mx="auto"
            sx={{
              WebkitMaskImage:
                "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M17 9V7a5 5 0 0 0-10 0v2H5v13h14V9h-2zM9 7a3 3 0 1 1 6 0v2H9V7z'/></svg>\")",
              WebkitMaskSize: "60%",
              WebkitMaskRepeat: "no-repeat",
              WebkitMaskPosition: "center",
            }}
          />
          <Text fontFamily="heading" fontSize="lg">
            {title}
          </Text>
          <Text fontSize="sm" color="ink.dim" lineHeight={1.7}>
            {description}
          </Text>
          <Button as={RouterLink} to="/settings/account" variant="fiscal" size="sm">
            Meer over Premium
          </Button>
        </VStack>
      </Box>
    </Box>
  );
}
