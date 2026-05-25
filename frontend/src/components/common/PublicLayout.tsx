import { Box, Container, Flex, Link } from "@chakra-ui/react";
import { Link as RouterLink, Outlet } from "react-router-dom";

import BrandMark from "./BrandMark";

export default function PublicLayout() {
  return (
    <Box className="app-shell" minH="100vh" position="relative" zIndex={2}>
      <Container maxW="container.xl" py={6}>
        <Flex justify="space-between" align="center" mb={{ base: 10, md: 16 }}>
          <BrandMark />
          <Flex gap={6} fontSize="sm">
            <Link as={RouterLink} to="/login" color="ink.dim" _hover={{ color: "ink.primary" }}>
              Inloggen
            </Link>
            <Link as={RouterLink} to="/register" color="azure.500" _hover={{ color: "azure.600" }}>
              Registreren
            </Link>
          </Flex>
        </Flex>
      </Container>

      <Container maxW="container.xl" pb={16}>
        <Outlet />
      </Container>
    </Box>
  );
}
