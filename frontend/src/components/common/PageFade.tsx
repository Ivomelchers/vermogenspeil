import { Box, type BoxProps } from "@chakra-ui/react";

export default function PageFade({ children, ...props }: BoxProps) {
  return (
    <Box
      animation="viewIn 0.45s cubic-bezier(0.2, 0.8, 0.2, 1) forwards"
      {...props}
    >
      {children}
    </Box>
  );
}
