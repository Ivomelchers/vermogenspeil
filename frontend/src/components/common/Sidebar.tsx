import { Badge, Box, Button, Flex, Text, VStack } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { NavLink, useLocation } from "react-router-dom";

import { useUser } from "../../contexts/UserContext";
import BrandMark from "./BrandMark";
import Kicker from "./Kicker";

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
        transition="background 0.2s ease, color 0.2s ease"
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

      {!permissions.isPremium && (
        <Box mx={4} mb={2} p={4} bg="gold.50" border="1px solid" borderColor="gold.500" borderRadius="base">
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

