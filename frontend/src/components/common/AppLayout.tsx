import { Box, Flex, Text } from "@chakra-ui/react";
import { useLocation } from "react-router-dom";

import AnimatedOutlet from "../layout/AnimatedOutlet";
import { relevantTaxYear } from "../../utils/taxYear";
import Kicker from "./Kicker";
import Sidebar from "./Sidebar";

const crumbMap: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/portfolio": "Portefeuille",
  "/transactions": "Transacties",
  "/belasting": "Belastingpositie",
  "/belasting/werkelijk": "Werkelijk rendement",
  "/belasting/overig-vermogen": "Overig vermogen",
  "/platforms": "Mijn platformen",
  "/platforms/add": "Nieuwe databron",
  "/platforms/vergelijker": "Platformen vergelijken",
  "/settings/account": "Account",
  "/settings/2fa": "Beveiliging",
  "/onboarding": "Onboarding",
};

function useCrumbs(pathname: string): { section: string; page: string } {
  const page = crumbMap[pathname] ?? "Overzicht";
  if (pathname.startsWith("/belasting")) {
    return { section: "Fiscaal", page };
  }
  if (pathname.startsWith("/platforms")) {
    return { section: "Platformen", page };
  }
  if (pathname.startsWith("/settings")) {
    return { section: "Account", page };
  }
  if (pathname.startsWith("/portfolio")) {
    return { section: "Overzicht", page };
  }
  return { section: "Overzicht", page };
}

export default function AppLayout() {
  const location = useLocation();
  const { section, page } = useCrumbs(location.pathname);
  const isDashboard = location.pathname === "/dashboard";
  const taxYear = relevantTaxYear();

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
            gap={4}
            flexWrap="wrap"
          >
            <Kicker letterSpacing="0.14em">
              {section} /{" "}
              <Text as="span" color="ink.primary" fontWeight={500}>
                {page}
              </Text>
            </Kicker>

            <Flex gap={3} align="center" flexWrap="wrap">
              <Flex
                align="center"
                gap={2}
                px={2.5}
                py={1.5}
                border="1px solid"
                borderColor="line.DEFAULT"
                borderRadius="sm"
                fontSize="meta"
                color="ink.dim"
                letterSpacing="0.06em"
                sx={{
                  fontFeatureSettings: '"tnum" 1',
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                <Box
                  w="6px"
                  h="6px"
                  borderRadius="full"
                  bg="moss.500"
                  animation="pulseLive 2s ease-in-out infinite"
                />
                Live koersen
              </Flex>
              <Flex
                px={2.5}
                py={1.5}
                border="1px solid"
                borderColor="line.DEFAULT"
                borderRadius="sm"
                fontSize="meta"
                color="ink.dim"
                letterSpacing="0.06em"
                sx={{
                  fontFeatureSettings: '"tnum" 1',
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                Peildatum 1 jan {taxYear}
              </Flex>
            </Flex>
          </Flex>

          <Box
            px={{ base: 6, md: 12 }}
            py={isDashboard ? { base: 0, md: 0 } : { base: 8, md: 10 }}
            overflow="hidden"
          >
            <AnimatedOutlet />
          </Box>
        </Box>
      </Flex>
    </Box>
  );
}
