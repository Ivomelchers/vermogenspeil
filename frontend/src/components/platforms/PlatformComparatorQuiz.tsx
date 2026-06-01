import { useState } from "react";
import {
  Box,
  Button,
  Flex,
  Radio,
  RadioGroup,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import type { CatalogPlatform } from "../../data/platformCatalog";
import FiscalCard from "../common/FiscalCard";
import {
  quizReasonForPlatform,
  scorePlatformQuiz,
  type QuizAnswers,
} from "../../utils/platformComparatorQuiz";
import PlatformAvatar from "./PlatformAvatar";

const INITIAL: QuizAnswers = {
  q1: null,
  q2: null,
  q3: null,
  q4: null,
  q5: null,
};

export default function PlatformComparatorQuiz() {
  const [answers, setAnswers] = useState<QuizAnswers>(INITIAL);
  const [result, setResult] = useState<CatalogPlatform | null>(null);
  const [validationHint, setValidationHint] = useState("");

  function setAnswer(key: keyof QuizAnswers, value: string) {
    setAnswers((prev) => ({ ...prev, [key]: value }));
    setValidationHint("");
  }

  function handleSubmit() {
    const incomplete = Object.values(answers).some((v) => v === null);
    if (incomplete) {
      setValidationHint("Beantwoord alle vragen om een aanbeveling te zien.");
      return;
    }
    setResult(scorePlatformQuiz(answers));
  }

  function handleReset() {
    setAnswers(INITIAL);
    setResult(null);
    setValidationHint("");
  }

  return (
    <FiscalCard elevated p={5} position="sticky" top={24}>
      <Text fontFamily="heading" fontSize="lg" mb={1}>
        Korte vragenlijst
      </Text>
      <Text fontSize="sm" color="ink.dim" mb={5} lineHeight={1.65}>
        Beantwoord 5 vragen voor een indicatief platform op basis van uw profiel.
      </Text>

      {result ? (
        <Box>
          <Text fontSize="xs" color="ink.faint" letterSpacing="0.12em" textTransform="uppercase" mb={3}>
            Aanbeveling
          </Text>
          <Flex gap={3} align="center" mb={3}>
            <PlatformAvatar initials={result.initials} color={result.color} />
            <Box>
              <Text fontWeight={600} fontFamily="heading" fontSize="lg">
                {result.name}
              </Text>
              <Text fontSize="sm" color="ink.dim">
                {result.country}
              </Text>
            </Box>
          </Flex>
          <Text fontSize="sm" color="ink.dim" lineHeight={1.65} mb={4}>
            {quizReasonForPlatform(result)}
          </Text>
          <Flex gap={2} flexDirection="column">
            <Button
              as={RouterLink}
              to={`/platforms/add?platform=${result.id}`}
              variant="fiscal"
              size="sm"
            >
              Bekijk koppelopties
            </Button>
            <Button variant="ghostNav" size="sm" onClick={handleReset}>
              Opnieuw
            </Button>
          </Flex>
        </Box>
      ) : (
        <VStack align="stretch" spacing={5}>
          <QuizQuestion
            label="1. Wat wilt u vooral beleggen?"
            value={answers.q1}
            onChange={(v) => setAnswer("q1", v)}
            options={[
              { value: "crypto", label: "Crypto" },
              { value: "stocks", label: "Aandelen & ETF's" },
              { value: "metals", label: "Edelmetaal" },
              { value: "mix", label: "Mix van alles" },
            ]}
          />
          <QuizQuestion
            label="2. Ervaring"
            value={answers.q2}
            onChange={(v) => setAnswer("q2", v)}
            options={[
              { value: "beginner", label: "Starter" },
              { value: "intermediate", label: "Enige ervaring" },
              { value: "advanced", label: "Ervaren" },
            ]}
          />
          <QuizQuestion
            label="3. Wat is het belangrijkst?"
            value={answers.q3}
            onChange={(v) => setAnswer("q3", v)}
            options={[
              { value: "simple", label: "Eenvoud" },
              { value: "cheap", label: "Lage kosten" },
              { value: "features", label: "Veel functies" },
              { value: "dutch", label: "Nederlands & AFM" },
            ]}
          />
          <QuizQuestion
            label="4. Beleggingsfrequentie"
            value={answers.q4}
            onChange={(v) => setAnswer("q4", v)}
            options={[
              { value: "dca", label: "Maandelijks (DCA)" },
              { value: "occasional", label: "Af en toe" },
              { value: "frequent", label: "Actief / dagelijks" },
            ]}
          />
          <QuizQuestion
            label="5. Automatische koppeling gewenst?"
            value={answers.q5}
            onChange={(v) => setAnswer("q5", v)}
            options={[
              { value: "api", label: "Ja, via API" },
              { value: "manual", label: "Nee, handmatig is ok" },
            ]}
          />
          {validationHint && (
            <Text fontSize="sm" color="rust.500">
              {validationHint}
            </Text>
          )}
          <Button variant="fiscal" w="full" onClick={handleSubmit}>
            Zie mijn aanbeveling
          </Button>
        </VStack>
      )}
    </FiscalCard>
  );
}

function QuizQuestion({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string | null;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <Box>
      <Text fontSize="sm" fontWeight={500} mb={2}>
        {label}
      </Text>
      <RadioGroup value={value ?? ""} onChange={onChange}>
        <Stack spacing={2}>
          {options.map((opt) => (
            <Radio key={opt.value} value={opt.value} size="sm" colorScheme="blue">
              <Text fontSize="sm">{opt.label}</Text>
            </Radio>
          ))}
        </Stack>
      </RadioGroup>
    </Box>
  );
}
