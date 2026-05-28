import { Box, Text } from "@chakra-ui/react";

interface AuthAlertProps {
  tone: "success" | "error" | "info";
  children: React.ReactNode;
}

const toneStyles = {
  success: {
    bg: "moss.50",
    borderColor: "moss.500",
    color: "moss.500",
  },
  error: {
    bg: "rust.50",
    borderColor: "rust.500",
    color: "rust.500",
  },
  info: {
    bg: "azure.50",
    borderColor: "azure.500",
    color: "azure.500",
  },
} as const;

export default function AuthAlert({ tone, children }: AuthAlertProps) {
  const styles = toneStyles[tone];

  return (
    <Box
      px={4}
      py={3}
      border="1px solid"
      borderColor={styles.borderColor}
      borderLeft="3px solid"
      borderLeftColor={styles.borderColor}
      borderRadius="sm"
      bg={styles.bg}
    >
      <Text fontSize="sm" lineHeight={1.7} color={styles.color}>
        {children}
      </Text>
    </Box>
  );
}
