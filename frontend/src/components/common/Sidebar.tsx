import { Box, Button, Flex, Text, VStack } from "@chakra-ui/react";
import { NavLink, useLocation } from "react-router-dom";

import BrandMark from "./BrandMark";
import Kicker from "./Kicker";

interface NavItem {
  label: string;
  to: string;
  premium?: boolean;
}

const navSections: { label: string; items: NavItem[] }[] = [
  {
    label: "Overzicht",
    items: [
      { label: "Dashboard", to: "/dashboard" },
      { label: "Portefeuille", to: "/dashboard" },
      { label: "Transacties", to: "/dashboard" },
    ],
  },
  {
    label: "Belasting",
    items: [
      { label: "Belastingpositie", to: "/dashboard", premium: true },
      { label: "Werkelijk rendement", to: "/dashboard", premium: true },
    ],
  },
];

function NavButton({ item }: { item: NavItem }) {
  const location = useLocation();
  const isActive = location.pathname === item.to;

  return (
    <Button
      as={NavLink}
      to={item.to}
      variant="ghostNav"
      position="relative"
      color={isActive ? "ink.primary" : "ink.dim"}
      bg={isActive ? "backgroundHover" : "transparent"}
      _before={
        isActive
          ? {
              content: '""',
              position: "absolute",
              left: "-16px",
              top: "50%",
              transform: "translateY(-50%)",
              w: "2px",
              h: "18px",
              bg: "azure.500",
            }
          : undefined
      }
    >
      <Box as="span" w="6px" h="6px" borderRadius="full" bg="currentColor" opacity={0.4} />
      {item.label}
      {item.premium && (
        <Box
          as="span"
          ml={1}
          w="11px"
          h="11px"
          display="inline-block"
          bg="azure.500"
          sx={{
            WebkitMaskImage:
              "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='M17 9V7a5 5 0 0 0-10 0v2H5v13h14V9h-2zM9 7a3 3 0 1 1 6 0v2H9V7z'/></svg>\")",
            WebkitMaskSize: "contain",
            WebkitMaskRepeat: "no-repeat",
            WebkitMaskPosition: "center",
          }}
        />
      )}
    </Button>
  );
}

export default function Sidebar() {
  return (
    <Box
      as="aside"
      bg="backgroundCard"
      borderRight="1px solid"
      borderColor="line.DEFAULT"
      w="240px"
      minH="100vh"
      position="sticky"
      top={0}
      display={{ base: "none", lg: "flex" }}
      flexDirection="column"
      py={8}
    >
      <Box px={7} pb={7} borderBottom="1px solid" borderColor="line.soft">
        <BrandMark to="/dashboard" />
        <Kicker mt={2} color="azure.500">
          Box 3 · Forfaitair
        </Kicker>
      </Box>

      <VStack align="stretch" spacing={0} px={4} py={6} flex={1}>
        {navSections.map((section) => (
          <Box key={section.label} mb={4}>
            <Kicker px={3} pb={2} pt={section.label === "Overzicht" ? 0 : 4}>
              {section.label}
            </Kicker>
            <VStack align="stretch" spacing={0.5}>
              {section.items.map((item) => (
                <NavButton key={`${section.label}-${item.label}`} item={item} />
              ))}
            </VStack>
          </Box>
        ))}

        <FiscalNote />
      </VStack>

      <Box px={7} pt={5} borderTop="1px solid" borderColor="line.soft">
        <Flex align="center" gap={3} p={2.5} borderRadius="base" bg="backgroundHover">
          <Flex
            w={8}
            h={8}
            borderRadius="full"
            align="center"
            justify="center"
            bgGradient="linear(135deg, azure.500, rust.500)"
            color="background"
            fontFamily="heading"
            fontWeight={600}
            fontSize="13px"
          >
            JV
          </Flex>
          <Box fontSize="12px" lineHeight={1.3}>
            <Text fontWeight={500}>Jan Vermeer</Text>
            <Kicker color="azure.500" letterSpacing="0.1em">
              Gratis
            </Kicker>
          </Box>
        </Flex>
      </Box>
    </Box>
  );
}

function FiscalNote() {
  return (
    <Box
      mx={4}
      mt={2}
      p={3.5}
      bg="azure.50"
      border="1px solid"
      borderColor="azure.300"
      borderLeft="3px solid"
      borderLeftColor="azure.500"
      borderRadius="sm"
    >
      <Text
        fontFamily="heading"
        fontStyle="italic"
        fontSize="12px"
        lineHeight={1.6}
        color="ink.primary"
      >
        Premium ontgrendelt werkelijk rendement en volledige Box 3-berekening.
      </Text>
    </Box>
  );
}
