import { Box } from "@chakra-ui/react";

import MoneyText from "../common/MoneyText";
import { formatEurParts } from "../../utils/formatMoney";

interface DisplayMoneyProps {
  amount: string | number;
  size?: "lg" | "md";
}

export default function DisplayMoney({ amount, size = "lg" }: DisplayMoneyProps) {
  const { whole, fraction } = formatEurParts(amount);
  const fractionSize = size === "lg" ? { base: "28px", md: "36px" } : { base: "20px", md: "24px" };

  return (
    <MoneyText variant="display" fontSize={size === "lg" ? undefined : { base: "40px", md: "48px" }}>
      <Box
        as="span"
        fontSize={size === "lg" ? { base: "28px", md: "32px" } : { base: "22px", md: "26px" }}
        color="ink.dim"
        fontStyle="italic"
        fontWeight={300}
      >
        €
      </Box>{" "}
      {whole}
      <Box as="span" fontSize={fractionSize} color="ink.dim" fontWeight={300}>
        ,{fraction}
      </Box>
    </MoneyText>
  );
}
