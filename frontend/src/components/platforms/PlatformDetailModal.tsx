import {
  Badge,
  Box,
  Button,
  Flex,
  List,
  ListItem,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import type { CatalogPlatform } from "../../data/platformCatalog";
import StarRating from "../common/StarRating";
import PlatformAvatar from "./PlatformAvatar";

interface PlatformDetailModalProps {
  platform: CatalogPlatform | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function PlatformDetailModal({
  platform,
  isOpen,
  onClose,
}: PlatformDetailModalProps) {
  if (!platform) return null;

  const isLive = platform.liveConnection != null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader fontFamily="heading" fontWeight={400}>
          <Flex align="center" gap={3}>
            <PlatformAvatar initials={platform.initials} color={platform.color} />
            <Box>
              {platform.name}
              <Text fontSize="sm" color="ink.dim" fontWeight={400}>
                {platform.country}
              </Text>
            </Box>
          </Flex>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Text fontSize="sm" color="ink.dim" lineHeight={1.7} mb={4}>
            {platform.description}
          </Text>
          <Flex gap={2} mb={4} flexWrap="wrap">
            <Badge variant="subtle">{platform.typeLabel}</Badge>
            {isLive ? (
              <Badge colorScheme="green">Nu koppelbaar</Badge>
            ) : (
              <Badge colorScheme="gray">Catalogus · koppeling volgt</Badge>
            )}
          </Flex>
          <Box bg="backgroundHover" p={3} borderRadius="sm" mb={4}>
            <Text fontSize="xs" color="ink.faint" textTransform="uppercase" letterSpacing="0.1em">
              Ideaal voor
            </Text>
            <Text fontWeight={500}>{platform.idealFor}</Text>
          </Box>
          {(
            [
              ["Kosten", platform.costStars, platform.costNote],
              ["Gebruik", platform.easeStars, platform.easeNote],
            ] as const
          ).map(([label, stars, note]) => (
            <Box key={label} mb={3}>
              <Text fontSize="xs" color="ink.faint" mb={1}>
                {label}
              </Text>
              <StarRating filled={stars} />
              <Text fontSize="sm" color="ink.dim" mt={1}>
                {note}
              </Text>
            </Box>
          ))}
          <Text fontSize="xs" color="ink.faint" mb={1}>
            Kenmerken
          </Text>
          <List spacing={1} fontSize="sm" color="ink.dim" mb={4}>
            {platform.features.map((f) => (
              <ListItem key={f}>· {f}</ListItem>
            ))}
          </List>
        </ModalBody>
        <ModalFooter gap={2}>
          <Button variant="fiscalOutline" onClick={onClose}>
            Sluiten
          </Button>
          <Button
            as={RouterLink}
            to={`/platforms/add?platform=${platform.id}&method=${platform.methods[0]}`}
            variant="fiscal"
            onClick={onClose}
          >
            {isLive ? "Nu koppelen" : "Bekijk koppelopties"}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
