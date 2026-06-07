import { Badge, type BadgeProps } from "@chakra-ui/react";

import {
  transactionTypeColor,
  transactionTypeLabel,
} from "../../utils/transactionLabels";

interface TransactionTypeBadgeProps extends BadgeProps {
  type: string;
}

export default function TransactionTypeBadge({
  type,
  ...props
}: TransactionTypeBadgeProps) {
  return (
    <Badge
      variant="subtle"
      colorScheme={transactionTypeColor(type)}
      fontWeight={600}
      fontSize="10px"
      letterSpacing="0.04em"
      px={2}
      py={0.5}
      borderRadius="sm"
      {...props}
    >
      {transactionTypeLabel(type)}
    </Badge>
  );
}
