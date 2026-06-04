import { useState } from "react";
import {
  Box,
  Button,
  Flex,
  Heading,
  Progress,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { completeOnboarding } from "../api/auth";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import { useUser } from "../contexts/UserContext";
import { getApiErrorMessage } from "../utils/apiError";

const STEPS = [
  {
    title: "Welkom bij Verbox",
    body: [
      "U ziet hier uw vermogen en een voorbereiding op Box 3 — forfaitair en (met Premium) werkelijk rendement.",
      "Dit is een hulpmiddel voor uw aangifte, geen officieel Belastingdienst-kanaal. Controleer altijd de definitieve cijfers.",
    ],
  },
  {
    title: "Vermogen vastleggen",
    body: [
      "Koppel een broker (Bitvavo, DEGIRO) of voer posities handmatig in.",
      "Zet per asset de fiscale categorie (belegging, banktegoed, schuld) op de portefeuillepagina.",
    ],
    cta: { label: "Platform koppelen", to: "/platforms/add" },
    ctaSecondary: { label: "Handmatige transactie", to: "/portfolio/manual/transaction" },
  },
  {
    title: "Belastingjaar & peildatum",
    body: [
      "Leg de peildatum vast op 1 januari — daarna berekent Verbox uw forfaitaire Box 3.",
      "Vul op /belasting eventueel banktegoeden, schulden en vastgoed aan en download een PDF-rapport.",
    ],
    cta: { label: "Naar belasting", to: "/belasting" },
    ctaSecondary: { label: "Dashboard", to: "/dashboard" },
  },
] as const;

export default function OnboardingPage() {
  const { user } = useUser();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const current = STEPS[step];
  const progress = ((step + 1) / STEPS.length) * 100;

  async function finish() {
    setBusy(true);
    setError("");
    try {
      await completeOnboarding();
      await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      navigate("/dashboard", { replace: true });
    } catch (finishError) {
      setError(getApiErrorMessage(finishError, "Onboarding afronden mislukt."));
    } finally {
      setBusy(false);
    }
  }

  function handleNext() {
    if (step < STEPS.length - 1) {
      setStep(step + 1);
      return;
    }
    void finish();
  }

  return (
    <Box minH="100vh" bg="background" px={6}>
    <VStack align="stretch" spacing={8} maxW="640px" mx="auto" py={{ base: 6, lg: 10 }}>
      <Box>
        <Kicker mb={2}>Start</Kicker>
        <Heading size="lg">
          {user?.first_name ? `Hoi ${user.first_name}` : "Aan de slag"}
        </Heading>
        <Progress value={progress} size="xs" mt={4} colorScheme="blue" borderRadius="full" />
        <Text fontSize="xs" color="ink.dim" mt={2}>
          Stap {step + 1} van {STEPS.length}
        </Text>
      </Box>

      {error && <AuthAlert tone="error">{error}</AuthAlert>}

      <FiscalCard p={6}>
        <Kicker mb={3}>{current.title}</Kicker>
        <VStack align="stretch" spacing={3}>
          {current.body.map((paragraph) => (
            <Text key={paragraph} color="ink.dim" fontSize="sm" lineHeight={1.75}>
              {paragraph}
            </Text>
          ))}
        </VStack>

        {"cta" in current && current.cta && (
          <Flex gap={2} flexWrap="wrap" mt={5}>
            <Button as={RouterLink} to={current.cta.to} variant="fiscalOutline" size="sm">
              {current.cta.label}
            </Button>
            {"ctaSecondary" in current && current.ctaSecondary && (
              <Button
                as={RouterLink}
                to={current.ctaSecondary.to}
                variant="ghostNav"
                size="sm"
              >
                {current.ctaSecondary.label}
              </Button>
            )}
          </Flex>
        )}
      </FiscalCard>

      <Flex justify="space-between" align="center" flexWrap="wrap" gap={3}>
        <Button
          variant="ghostNav"
          size="sm"
          isDisabled={step === 0 || busy}
          onClick={() => setStep(step - 1)}
        >
          Vorige
        </Button>
        <Button variant="fiscal" size="sm" isLoading={busy} onClick={() => void handleNext()}>
          {step < STEPS.length - 1 ? "Volgende" : "Naar dashboard"}
        </Button>
      </Flex>
    </VStack>
    </Box>
  );
}
