import { Badge, Box, Button, Flex, Text, VStack } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { NavLink, useLocation } from "react-router-dom";

import { useUser } from "../../contexts/UserContext";
import { fiscalScrollbarSx } from "../../styles/scrollbar";
import Kicker from "./Kicker";
import SidebarBrand from "./SidebarBrand";

interface NavItem {
  label: string;
  to: string;
}

const navSections: { label: string; items: NavItem[] }[] = [
  {
    label: "Overzicht",
    items: [
      { label: "Dashboard", to: "/dashboard" },
      { label: "Portefeuille", to: "/portfolio" },
      { label: "Asset toevoegen", to: "/portfolio/manual/asset" },
      { label: "Transactie toevoegen", to: "/portfolio/manual/transaction" },
      { label: "Transacties", to: "/transactions" },
    ],
  },
  {
    label: "Belasting",
    items: [
      { label: "Belastingpositie", to: "/belasting" },
      { label: "Werkelijk rendement", to: "/belasting/werkelijk" },
      { label: "Overig vermogen", to: "/belasting/overig-vermogen" },
    ],
  },
  {
    label: "Platformen",
    items: [
      { label: "Mijn platformen", to: "/platforms" },
      { label: "Platform toevoegen", to: "/platforms/add" },
      { label: "Platformen vergelijken", to: "/platforms/vergelijker" },
    ],
  },
  {
    label: "Account",
    items: [
      { label: "Account", to: "/settings/account" },
      { label: "2FA beveiliging", to: "/settings/2fa" },
    ],
  },
];

function NavButton({ item }: { item: NavItem }) {
  const location = useLocation();
  const isActive =
    item.to === "/belasting/werkelijk"
      ? location.pathname.startsWith("/belasting/werkelijk")
      : item.to === "/belasting/overig-vermogen"
        ? location.pathname.startsWith("/belasting/overig-vermogen")
      : item.to === "/belasting"
        ? location.pathname === "/belasting"
        : item.to === "/platforms/add"
          ? location.pathname.startsWith("/platforms/add")
          : location.pathname === item.to;

  return (
    <motion.div whileHover={{ x: 3 }} whileTap={{ scale: 0.98 }} transition={{ duration: 0.15 }}>
      <Button
        as={NavLink}
        to={item.to}
        variant="ghostNav"
        position="relative"
        w="full"
        color={isActive ? "ink.primary" : "ink.dim"}
        bg={isActive ? "backgroundHover" : "transparent"}
        fontWeight={isActive ? 500 : 400}
        transition="background 0.2s ease, color 0.2s ease"
        borderLeft="2px solid"
        borderLeftColor={isActive ? "azure.500" : "transparent"}
        borderRadius="base"
        pl={3}
      >
        {item.label}
      </Button>
    </motion.div>
  );
}

function getInitials(firstName: string, email: string): string {
  const trimmed = firstName.trim();
  if (trimmed) {
    const parts = trimmed.split(/\s+/);
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return trimmed.slice(0, 2).toUpperCase();
  }

  return email.slice(0, 2).toUpperCase();
}

export default function Sidebar() {
  const { user, permissions, logout } = useUser();
  const displayName = user?.full_name || user?.first_name || user?.email.split("@")[0] || "Account";
  const initials = getInitials(user?.first_name ?? "", user?.email ?? "??");
  const tierLabel = permissions.isPremium ? "Premium" : "Gratis";

  return (
    <Box
      as="aside"
      bg="backgroundCard"
      borderRight="1px solid"
      borderColor="line.DEFAULT"
      w="260px"
      h="100dvh"
      maxH="100vh"
      position="fixed"
      top={0}
      left={0}
      zIndex={20}
      display={{ base: "none", lg: "flex" }}
      flexDirection="column"
      overflow="hidden"
    >
      <Box
        px={5}
        h="96px"
        flexShrink={0}
        display="flex"
        alignItems="center"
        borderBottom="1px solid"
        borderColor="line.soft"
      >
        <SidebarBrand />
      </Box>

      {!permissions.isPremium && (
        <Box
          mx={4}
          mt={3}
          p={4}
          bg="gold.50"
          border="1px solid"
          borderColor="gold.500"
          borderRadius="base"
          flexShrink={0}
        >
          <Badge variant="premium" mb={2}>
            Premium
          </Badge>
          <Text fontSize="xs" color="ink.dim" lineHeight={1.5} mb={3}>
            Werkelijk rendement, Box 3-rapport en diepgaande portefeuille-analyse.
          </Text>
          <Button variant="premium" size="xs" w="full" isDisabled>
            Binnenkort beschikbaar
          </Button>
        </Box>
      )}

      <Box
        flex={1}
        minH={0}
        overflowY="auto"
        overscrollBehavior="contain"
        px={4}
        py={4}
        pr={3}
        sx={fiscalScrollbarSx("vertical")}
      >
        <VStack align="stretch" spacing={0}>
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
        </VStack>
      </Box>

      <Box
        px={5}
        py={4}
        borderTop="1px solid"
        borderColor="line.soft"
        flexShrink={0}
        bg="backgroundCard"
      >
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
            {initials}
          </Flex>
          <Box flex={1} fontSize="12px" lineHeight={1.3} minW={0}>
            <Text fontWeight={500} noOfLines={1}>
              {displayName}
            </Text>
            <Kicker
              color={permissions.isPremium ? "gold.500" : "azure.500"}
              letterSpacing="0.1em"
            >
              {tierLabel}
            </Kicker>
          </Box>
        </Flex>

        <Button
          variant="fiscalOutline"
          w="full"
          mt={3}
          size="sm"
          onClick={() => void logout()}
        >
          Uitloggen
        </Button>
      </Box>
    </Box>
  );
}

