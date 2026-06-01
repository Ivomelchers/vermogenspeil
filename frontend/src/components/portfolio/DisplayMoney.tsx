import { Box } from "@chakra-ui/react";

import MoneyText, { type MoneyTone } from "../common/MoneyText";
import { formatEurParts } from "../../utils/formatMoney";

const sizeScale = {
  lg: { base: "48px", md: "56px", lg: "64px" },
  md: { base: "36px", md: "44px" },
  sm: { base: "22px", md: "26px" },
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
      <Box as="span" fontSize="inherit" color="ink.dim" fontWeight={400}>
        €
      </Box>
      <Box as="span" fontSize="inherit" fontWeight={500} ml={1}>
        {whole}
      </Box>
      <Box as="span" fontSize="inherit" color="ink.dim" fontWeight={400}>
        ,{fraction}
      </Box>
    </MoneyText>
  );
}
