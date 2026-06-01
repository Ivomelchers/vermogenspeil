import { Box, SimpleGrid, Text } from "@chakra-ui/react";

export interface StatItem {
  label: string;
  value: string | number;
  sub: string;
  tone?: "default" | "moss" | "ochre";
}

interface StatStripProps {
  items: StatItem[];
  columns?: number;
}

/** stat-strip uit premium prototype */
export default function StatStrip({ items, columns = 4 }: StatStripProps) {
  return (
    <SimpleGrid columns={{ base: 2, md: columns }} spacing={4}>
      {items.map((item) => (
        <Box
          key={item.label}
          bg="backgroundCard"
          border="1px solid"
          borderColor="line.soft"
          borderRadius="base"
          px={5}
          py={4}
          transition="border-color 0.2s ease, box-shadow 0.2s ease"
          _hover={{ borderColor: "azure.300", boxShadow: "0 4px 20px rgba(26, 58, 92, 0.06)" }}
        >
          <Text
            fontSize="10px"
            letterSpacing="0.14em"
            textTransform="uppercase"
            color="ink.faint"
            mb={2}
          >
            {item.label}
          </Text>
          <Text
            fontFamily="heading"
            fontSize="2xl"
            letterSpacing="-0.02em"
            color={
              item.tone === "moss"
                ? "moss.500"
                : item.tone === "ochre"
                  ? "ochre.500"
                  : "ink.primary"
            }
          >
            {item.value}
          </Text>
          <Text fontSize="xs" color="ink.dim" mt={1}>
            {item.sub}
          </Text>
        </Box>
      ))}
    </SimpleGrid>
  );
}
