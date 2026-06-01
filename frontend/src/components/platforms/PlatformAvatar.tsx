import { Flex } from "@chakra-ui/react";

interface PlatformAvatarProps {
  initials: string;
  color?: string;
  size?: "sm" | "md";
}

export default function PlatformAvatar({
  initials,
  color = "#2d5a3a",
  size = "md",
}: PlatformAvatarProps) {
  const dim = size === "sm" ? 8 : 10;
  return (
    <Flex
      w={dim}
      h={dim}
      minW={dim}
      borderRadius="base"
      bg="backgroundHover"
      align="center"
      justify="center"
      fontFamily="heading"
      fontWeight={600}
      fontSize={size === "sm" ? "11px" : "13px"}
      color={color}
      letterSpacing="-0.02em"
    >
      {initials}
    </Flex>
  );
}
