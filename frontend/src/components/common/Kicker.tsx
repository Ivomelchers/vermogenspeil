import { Text, type TextProps } from "@chakra-ui/react";

export default function Kicker({ children, ...props }: TextProps) {
  return (
    <Text
      fontFamily="body"
      fontSize="kicker"
      letterSpacing="0.18em"
      textTransform="uppercase"
      color="ink.faint"
      fontVariantNumeric="tabular-nums"
      sx={{ fontFeatureSettings: '"tnum" 1' }}
      {...props}
    >
      {children}
    </Text>
  );
}
