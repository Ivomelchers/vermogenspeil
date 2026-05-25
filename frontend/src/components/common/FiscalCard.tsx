import { Box, type BoxProps } from "@chakra-ui/react";

export default function FiscalCard({ children, ...props }: BoxProps) {
  return (
    <Box
      bg="backgroundCard"
      border="1px solid"
      borderColor="line.DEFAULT"
      borderRadius="base"
      transition="border-color 0.15s ease"
      _hover={{ borderColor: "taupe.500" }}
      {...props}
    >
      {children}
    </Box>
  );
}
