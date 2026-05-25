import { Box, Flex } from "@chakra-ui/react";
import { Outlet, useLocation } from "react-router-dom";

import Kicker from "./Kicker";
import Sidebar from "./Sidebar";

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard",
};

export default function AppLayout() {
  const location = useLocation();
  const title = pageTitles[location.pathname] ?? "MijnVermogen";

  return (
    <Box className="app-shell">
      <Flex minH="100vh" position="relative" zIndex={2}>
        <Sidebar />

        <Box as="main" flex={1} minW={0}>
          <Flex
            px={{ base: 6, md: 12 }}
            py={6}
            borderBottom="1px solid"
            borderColor="line.DEFAULT"
            align="center"
            justify="space-between"
            bgGradient="linear(to-b, backgroundCard, background)"
          >
            <Kicker>MijnVermogen · {title}</Kicker>
            <Flex
              as="span"
              fontSize="meta"
              px={2.5}
              py={1.5}
              border="1px solid"
              borderColor="line.DEFAULT"
              borderRadius="sm"
              color="ink.dim"
              letterSpacing="0.06em"
              sx={{ fontFeatureSettings: '"tnum" 1', fontVariantNumeric: "tabular-nums" }}
            >
              Peildatum 1 jan 2026
            </Flex>
          </Flex>

          <Box px={{ base: 6, md: 12 }} py={{ base: 8, md: 10 }}>
            <Outlet />
          </Box>
        </Box>
      </Flex>
    </Box>
  );
}
