import { Text, type TextProps } from "@chakra-ui/react";

type MoneyVariant = "display" | "tabular" | "delta";
type MoneyTone = "default" | "positive" | "negative" | "accent";

const toneColor: Record<MoneyTone, string> = {
  default: "ink.primary",
  positive: "moss.500",
  negative: "rust.500",
  accent: "azure.500",
};

interface MoneyTextProps extends TextProps {
  variant?: MoneyVariant;
  tone?: MoneyTone;
}

export default function MoneyText({
  variant = "tabular",
  tone = "default",
  children,
  ...props
}: MoneyTextProps) {
  const isDisplay = variant === "display";
  const isDelta = variant === "delta";

  return (
    <Text
      color={toneColor[tone]}
      fontFamily={isDisplay ? "heading" : "body"}
      fontSize={isDisplay ? { base: "56px", md: "72px", lg: "88px" } : isDelta ? "13px" : "inherit"}
      fontWeight={isDisplay ? 400 : isDelta ? 400 : 500}
      lineHeight={isDisplay ? 1 : 1.4}
      letterSpacing={isDisplay ? "-0.03em" : isDelta ? "0.02em" : "normal"}
      fontVariantNumeric="tabular-nums"
      sx={{ fontFeatureSettings: '"tnum" 1' }}
      {...props}
    >
      {children}
    </Text>
  );
}
