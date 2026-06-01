import { type ReactNode } from "react";
import { Box, Table, type TableProps } from "@chakra-ui/react";

import FiscalCard from "./FiscalCard";

interface FiscalTableProps extends TableProps {
  children: ReactNode;
  toolbar?: ReactNode;
}

/** Premium tabel in elevated card met toolbar. */
export default function FiscalTable({ children, toolbar, ...tableProps }: FiscalTableProps) {
  return (
    <FiscalCard elevated p={0} overflow="hidden">
      {toolbar && (
        <Box
          px={5}
          py={3}
          borderBottom="1px solid"
          borderColor="line.soft"
          bg="backgroundHover"
        >
          {toolbar}
        </Box>
      )}
      <Box overflowX="auto">
        <Table
          size="sm"
          variant="simple"
          sx={{
            "th, td": {
              fontVariantNumeric: "tabular-nums",
              fontFeatureSettings: '"tnum" 1',
            },
            th: {
              fontFamily: "body",
              fontSize: "10px",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              color: "ink.faint",
              fontWeight: 600,
              borderColor: "line.soft",
            },
            td: {
              borderColor: "line.soft",
            },
            "tbody tr": {
              transition: "background 0.15s ease",
              _hover: { bg: "azure.50" },
            },
          }}
          {...tableProps}
        >
          {children}
        </Table>
      </Box>
    </FiscalCard>
  );
}
