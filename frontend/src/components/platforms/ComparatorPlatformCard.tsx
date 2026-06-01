import { Box, Button, Flex, List, ListItem, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import type { CatalogPlatform } from "../../data/platformCatalog";
import StarRating from "../common/StarRating";
import PlatformAvatar from "./PlatformAvatar";

interface ComparatorPlatformCardProps {
  platform: CatalogPlatform;
  onMoreInfo: () => void;
}

export default function ComparatorPlatformCard({
  platform,
  onMoreInfo,
}: ComparatorPlatformCardProps) {
  const intColor =
    platform.methods[0] === "api"
      ? "moss"
      : platform.methods[0] === "csv"
        ? "ochre"
        : "azure";
  const isLive = platform.liveConnection != null;

  return (
    <Box
      minW={{ base: "280px", md: "300px" }}
      maxW="320px"
      flex="0 0 auto"
      bg="backgroundCard"
      border="1px solid"
      borderColor="line.soft"
      borderRadius="base"
      p={5}
      display="flex"
      flexDirection="column"
      gap={3}
      transition="all 0.2s ease"
      _hover={{ borderColor: "azure.300", boxShadow: "0 8px 32px rgba(26, 58, 92, 0.08)" }}
    >
      <Flex gap={3} align="center">
        <PlatformAvatar initials={platform.initials} color={platform.color} />
        <Box flex={1}>
          <Flex align="center" gap={2} flexWrap="wrap">
            <Text fontFamily="heading" fontSize="lg" fontWeight={500}>
              {platform.name}
            </Text>
            {isLive && (
              <Text
                fontSize="9px"
                fontWeight={700}
                letterSpacing="0.08em"
                textTransform="uppercase"
                color="moss.500"
              >
                Live
              </Text>
            )}
          </Flex>
          <Text fontSize="xs" color="ink.dim">
            {platform.country}
          </Text>
        </Box>
      </Flex>

      <Box bg="backgroundHover" borderRadius="sm" px={3} py={2}>
        <Text fontSize="10px" letterSpacing="0.1em" textTransform="uppercase" color="ink.faint">
          Ideaal voor
        </Text>
        <Text fontSize="sm" fontWeight={500} mt={0.5}>
          {platform.idealFor}
        </Text>
      </Box>

      {(
        [
          ["Kosten", platform.costStars, platform.costNote],
          ["Aanbod", null, platform.offering],
          ["Regulering", null, platform.regulationBadge],
          ["Gebruik", platform.easeStars, platform.easeNote],
        ] as const
      ).map(([label, stars, note]) => (
        <Box key={label}>
          <Text fontSize="10px" color="ink.faint" letterSpacing="0.08em" textTransform="uppercase" mb={1}>
            {label}
          </Text>
          {stars != null && <StarRating filled={stars} />}
          <Text fontSize="sm" color="ink.dim" mt={1}>
            {note}
          </Text>
        </Box>
      ))}

      <Box>
        <Text fontSize="10px" color="ink.faint" letterSpacing="0.08em" textTransform="uppercase" mb={1}>
          Integratie
        </Text>
        <Flex align="center" gap={2}>
          <Text
            fontSize="xs"
            fontWeight={600}
            px={2}
            py={0.5}
            borderRadius="sm"
            bg={`${intColor}.50`}
            color={`${intColor}.600`}
            border="1px solid"
            borderColor={`${intColor}.200`}
          >
            {platform.integrationLabel}
          </Text>
          <Text fontSize="sm" color="ink.dim">
            {platform.integrationNote}
          </Text>
        </Flex>
      </Box>

      <Box flex={1}>
        <Text fontSize="10px" color="ink.faint" mb={1}>
          Kenmerken
        </Text>
        <List spacing={0.5} fontSize="sm" color="ink.dim">
          {platform.features.slice(0, 3).map((f) => (
            <ListItem key={f}>· {f}</ListItem>
          ))}
        </List>
      </Box>

      <Flex gap={2} mt={2}>
        <Button variant="fiscalOutline" size="sm" flex={1} onClick={onMoreInfo}>
          Meer info
        </Button>
        <Button
          as={RouterLink}
          to={`/platforms/add?platform=${platform.id}&method=${platform.methods[0]}`}
          variant="fiscal"
          size="sm"
          flex={1}
        >
          Koppelen
        </Button>
      </Flex>
    </Box>
  );
}
