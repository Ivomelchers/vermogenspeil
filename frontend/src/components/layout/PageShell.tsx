import { type ReactNode } from "react";
import { Box, type BoxProps, VStack } from "@chakra-ui/react";

interface PageShellProps extends BoxProps {
  children: ReactNode;
  /** Geen max-width (dashboard full-bleed) */
  wide?: boolean;
  spacing?: number;
}

/** Standaard pagina-wrapper — geen motion (route-fade zit in AnimatedOutlet). */
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
      <VStack align="stretch" spacing={spacing}>
        {children}
      </VStack>
    </Box>
  );
}
