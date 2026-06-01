import { HStack, Text } from "@chakra-ui/react";

interface StarRatingProps {
  filled: number;
  max?: number;
}

export default function StarRating({ filled, max = 5 }: StarRatingProps) {
  return (
    <HStack spacing={0} fontSize="sm" lineHeight={1}>
      {Array.from({ length: max }, (_, i) => (
        <Text
          key={i}
          as="span"
          color={i < filled ? "ochre.500" : "line.DEFAULT"}
        >
          ★
        </Text>
      ))}
    </HStack>
  );
}
