import { Box, Image } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import { logoSrc, type BrandLogoVariant } from "../../brand/paths";

interface BrandMarkProps {
  to?: string;
  variant?: BrandLogoVariant;
  /** Donkere achtergrond → reversed logo */
  reversed?: boolean;
  height?: number | string;
}

export default function BrandMark({
  to = "/",
  variant = "horizontal",
  reversed = false,
  height = 36,
}: BrandMarkProps) {
  return (
    <Box
      as={RouterLink}
      to={to}
      display="inline-flex"
      alignItems="center"
      _hover={{ textDecoration: "none", opacity: 0.92 }}
    >
      <Image
        src={logoSrc(variant, reversed)}
        alt="Verbox"
        h={height}
        w="auto"
        maxW="100%"
        objectFit="contain"
        loading="eager"
      />
    </Box>
  );
}
