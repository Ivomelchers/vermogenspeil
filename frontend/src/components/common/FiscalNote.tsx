import { Box, type BoxProps } from "@chakra-ui/react";

/** note-fiscal uit premium prototype */
export default function FiscalNote({ children, ...props }: BoxProps) {
  return (
    <Box
      bg="azure.100"
      border="1px solid"
      borderColor="azure.300"
      borderLeft="3px solid"
      borderLeftColor="azure.500"
      borderRadius="sm"
      px={5}
      py={4}
      fontFamily="heading"
      fontStyle="italic"
      fontSize="sm"
      color="ink.primary"
      lineHeight={1.65}
      sx={{
        strong: { color: "azure.500", fontStyle: "normal", fontWeight: 600 },
      }}
      {...props}
    >
      {children}
    </Box>
  );
}
