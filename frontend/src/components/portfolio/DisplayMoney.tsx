import { Box } from "@chakra-ui/react";

import MoneyText, { type MoneyTone } from "../common/MoneyText";
import { formatEurParts } from "../../utils/formatMoney";

const sizeScale = {
  hero: { base: "52px", md: "72px", lg: "88px" },
  lg: { base: "48px", md: "56px", lg: "64px" },
  md: { base: "36px", md: "44px" },
  sm: { base: "22px", md: "26px" },
} as const;

const currencyScale = {
  hero: { base: "22px", md: "28px", lg: "32px" },
  lg: { base: "20px", md: "24px" },
  md: { base: "18px", md: "20px" },
  sm: { base: "14px", md: "16px" },
} as const;

const fractionScale = {
  hero: { base: "24px", md: "32px", lg: "36px" },
  lg: { base: "20px", md: "24px" },
  md: { base: "16px", md: "18px" },
  sm: { base: "12px", md: "14px" },
} as const;

interface DisplayMoneyProps {
  amount: string | number;
  size?: keyof typeof sizeScale;
  tone?: MoneyTone;
  /** Prefix + or − based on sign (zero has no prefix). */
  signed?: boolean;
}

export default function DisplayMoney({
  amount,
  size = "lg",
  tone = "default",
  signed = false,
}: DisplayMoneyProps) {
  const numeric = typeof amount === "string" ? parseFloat(amount) : amount;
  const safe = Number.isNaN(numeric) ? 0 : numeric;
  const { whole, fraction } = formatEurParts(Math.abs(safe));
  const prefix =
    signed && safe > 0 ? "+ " : signed && safe < 0 ? "− " : "";

  return (
    <MoneyText
      variant="display"
      tone={tone}
      fontFamily="body"
      fontSize={sizeScale[size]}
      lineHeight={1}
      display="inline-flex"
      alignItems="baseline"
      flexWrap="nowrap"
      whiteSpace="nowrap"
      gap={0}
    >
      {prefix ? (
        <Box as="span" fontSize="inherit" fontWeight={500}>
          {prefix}
        </Box>
      ) : null}
      <Box as="span" fontSize={currencyScale[size]} color="ink.dim" fontWeight={300}>
        €
      </Box>
      <Box as="span" fontSize="inherit" fontWeight={400} ml={1} letterSpacing="-0.03em">
        {whole}
      </Box>
      <Box as="span" fontSize={fractionScale[size]} color="ink.dim" fontWeight={300}>
        ,{fraction}
      </Box>
    </MoneyText>
  );
}
