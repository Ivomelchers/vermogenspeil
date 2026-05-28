import { Flex, Spinner } from "@chakra-ui/react";

export default function AuthLoading() {
  return (
    <Flex className="app-shell" minH="100vh" align="center" justify="center">
      <Spinner color="azure.500" size="lg" />
    </Flex>
  );
}
