import { Box, Image } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import { brandPaths } from "../../brand/paths";

/** Vaste hoogte logo-zone in sidebar-header. */
export const SIDEBAR_LOGO_SLOT_H = "80px";

export default function SidebarBrand() {
  return (
    <Box
      as={RouterLink}
      to="/dashboard"
      display="block"
      h={SIDEBAR_LOGO_SLOT_H}
      w="100%"
      maxW="220px"
      overflow="hidden"
      flexShrink={0}
      _hover={{ textDecoration: "none", opacity: 0.92 }}
    >
      <Image
        src={brandPaths.logoHorizontal}
        alt="Verbox"
        h="80px"
        w="100%"
        maxW="100%"
        objectFit="contain"
        objectPosition="left top"
        loading="eager"
      />
    </Box>
  );
}
