import { Box, type BoxProps } from "@chakra-ui/react";

interface FiscalCardProps extends BoxProps {
  elevated?: boolean;
}

export default function FiscalCard({ children, elevated, ...props }: FiscalCardProps) {
  return (
    <Box
      bg={elevated ? "paper" : "backgroundCard"}
      border="1px solid"
      borderColor="line.DEFAULT"
      borderRadius="base"
      boxShadow={elevated ? "md" : "none"}
      transition="border-color 0.15s ease, box-shadow 0.15s ease"
      _hover={{
        borderColor: "taupe.500",
        boxShadow: elevated ? "md" : "sm",
      }}
      {...props}
    >
      {children}
    </Box>
  );
}
