import { Box, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

interface BrandMarkProps {
  to?: string;
}

export default function BrandMark({ to = "/" }: BrandMarkProps) {
  return (
    <Box
      as={RouterLink}
      to={to}
      display="flex"
      alignItems="baseline"
      gap="2px"
      _hover={{ textDecoration: "none" }}
    >
      <Text
        as="span"
        fontFamily="heading"
        fontWeight={500}
        fontSize="22px"
        letterSpacing="-0.01em"
        color="ink.primary"
      >
        Mijn
        <Text as="em" fontStyle="italic" color="azure.500">
          Vermogen
        </Text>
      </Text>
    </Box>
  );
}
