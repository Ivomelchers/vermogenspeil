import { Box, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { motion } from "framer-motion";

import type { CatalogPlatform } from "../../data/platformCatalog";
import { staggerItem } from "../layout/motion";

interface PlatformBrowseCardProps {
  platform: CatalogPlatform;
}

export default function PlatformBrowseCard({ platform }: PlatformBrowseCardProps) {
  const method = platform.methods[0];
  const caption =
    method === "api"
      ? "+ Koppeling aanmaken"
      : method === "csv"
        ? "+ Bestand uploaden"
        : method === "year"
          ? "+ Jaaropgave uploaden"
          : "+ Handmatig invoegen";

  return (
    <motion.div variants={staggerItem} whileHover={{ y: -3 }} transition={{ duration: 0.2 }}>
      <Box
        as={RouterLink}
        to={`/platforms/add?platform=${platform.id}`}
        display="block"
        p={5}
        bg="backgroundCard"
        border="1px solid"
        borderColor="line.soft"
        borderRadius="base"
        h="full"
        transition="all 0.2s ease"
        _hover={{
          borderColor: "azure.400",
          boxShadow: "0 8px 28px rgba(26, 58, 92, 0.08)",
          textDecoration: "none",
        }}
      >
        <Text fontSize="10px" letterSpacing="0.12em" textTransform="uppercase" color="ink.faint" mb={2}>
          {platform.typeLabel.split(" · ").slice(0, 2).join(" · ")}
        </Text>
        <Text fontFamily="heading" fontSize="lg" fontWeight={500} mb={3}>
          {platform.name}
        </Text>
        <Text fontSize="sm" color="ink.dim" lineHeight={1.65} mb={4} noOfLines={3}>
          {platform.features[0]} · {platform.integrationNote}
        </Text>
        <Text fontSize="xs" color="azure.500" fontWeight={500}>
          {caption}
        </Text>
      </Box>
    </motion.div>
  );
}
