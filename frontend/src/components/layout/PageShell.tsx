import { type ReactNode } from "react";
import { Box, type BoxProps } from "@chakra-ui/react";
import { motion } from "framer-motion";

import { staggerContainer } from "./motion";

interface PageShellProps extends BoxProps {
  children: ReactNode;
  /** Geen max-width (dashboard full-bleed) */
  wide?: boolean;
  spacing?: number;
}

/**
 * Standaard pagina-wrapper: max-width, verticale rhythm, stagger-animatie voor kinderen.
 */
export default function PageShell({
  children,
  wide = false,
  spacing = 10,
  ...props
}: PageShellProps) {
  return (
    <Box
      maxW={wide ? "none" : "1280px"}
      mx={wide ? 0 : "auto"}
      w="full"
      pb={12}
      {...props}
    >
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        style={{ display: "flex", flexDirection: "column", gap: `${spacing * 4}px` }}
      >
        {children}
      </motion.div>
    </Box>
  );
}
