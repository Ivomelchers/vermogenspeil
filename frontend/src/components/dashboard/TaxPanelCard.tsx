import { type ReactNode } from "react";
import { Badge, Box, Button, Flex, Grid, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import type { ForfaitairBox3Summary } from "../../api/tax";
import type { PeildatumSnapshot } from "../../api/snapshots";
import Kicker from "../common/Kicker";
import MoneyText from "../common/MoneyText";
import { formatEur } from "../../utils/formatMoney";

interface TaxPanelCardProps {
  taxYear: number;
  forfaitair: ForfaitairBox3Summary | null;
  peildatum: PeildatumSnapshot | null;
  hasPositions: boolean;
  snapshotBusy: boolean;
  onCreatePeildatum: () => void;
  snapshotMessage?: string;
}

function TaxMetric({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: boolean;
}) {
  return (
    <Box>
      <Kicker mb={1.5} fontSize="9px">
        {label}
      </Kicker>
      {typeof value === "string" ? (
        <MoneyText
          variant="display"
          fontSize="28px"
          color={accent ? "azure.500" : "ink.primary"}
          letterSpacing="-0.02em"
        >
          {value}
        </MoneyText>
      ) : (
        value
      )}
      {hint && (
        <Text fontSize="xs" color="ink.dim" mt={1} fontStyle="italic" fontFamily="heading">
          {hint}
        </Text>
      )}
    </Box>
  );
}

export default function TaxPanelCard({
  taxYear,
  forfaitair,
  peildatum,
  hasPositions,
  snapshotBusy,
  onCreatePeildatum,
  snapshotMessage,
}: TaxPanelCardProps) {
  const box3 = forfaitair?.box3_inputs;

  return (
    <Box
      position="relative"
      overflow="hidden"
      bgGradient="linear(to-b, backgroundCard, backgroundHover)"
      border="1px solid"
      borderColor="line.DEFAULT"
      borderRadius="base"
      p={{ base: 5, md: 7 }}
      h="full"
      _before={{
        content: '""',
        position: "absolute",
        top: 0,
        right: 0,
        w: "140px",
        h: "140px",
        bgGradient: "radial(circle, azure.100, transparent 70%)",
        pointerEvents: "none",
      }}
    >
      <Flex justify="space-between" align="flex-start" mb={5} position="relative">
        <Box>
          <Text
            fontFamily="heading"
            fontSize="xl"
            letterSpacing="-0.01em"
            sx={{ em: { fontStyle: "italic", color: "azure.500" } }}
          >
            Belastingpositie <Text as="em">{taxYear}</Text>
          </Text>
          <Kicker mt={1}>Forfaitair stelsel · box 3</Kicker>
        </Box>
        <Badge variant="premium">Premium</Badge>
      </Flex>

      <Grid templateColumns="1fr 1fr" gap={5} mb={5} position="relative">
        <TaxMetric
          label="Te betalen"
          value={
            forfaitair?.available && forfaitair.tax_due_eur ? (
              formatEur(forfaitair.tax_due_eur)
            ) : (
              "—"
            )
          }
          hint={forfaitair?.available ? "voorlopig · forfaitair" : "peildatum vereist"}
          accent
        />
        <TaxMetric
          label="Peildatum"
          value={
            peildatum ? formatEur(peildatum.total_value_eur) : "—"
          }
          hint={peildatum ? "vastgelegd 1 jan" : "nog niet vastgelegd"}
        />
        {box3 && (
          <>
            <TaxMetric
              label="Beleggingen (O)"
              value={formatEur(box3.overige_bezittingen_eur)}
              hint="overige bezittingen"
            />
            <TaxMetric
              label="Bank (B)"
              value={formatEur(box3.banktegoeden_eur)}
              hint="banktegoeden"
            />
          </>
        )}
      </Grid>

      <Text fontSize="xs" color="ink.dim" lineHeight={1.55} mb={3} position="relative">
        {forfaitair?.available
          ? (forfaitair.disclaimer ?? "Fiscaal inzicht op basis van uw peildatum-snapshot.")
          : hasPositions
            ? `Leg peildatum ${taxYear} vast om Box 3 te berekenen.`
            : "Koppel een platform om te starten."}
      </Text>

      <Flex gap={2} flexWrap="wrap" position="relative">
        {forfaitair?.available && (
          <Button as={RouterLink} to="/belasting" variant="fiscal" size="sm">
            Belastingpositie
          </Button>
        )}
        {hasPositions && !peildatum && (
          <Button
            variant="fiscalOutline"
            size="sm"
            isLoading={snapshotBusy}
            onClick={onCreatePeildatum}
          >
            Peildatum vastleggen
          </Button>
        )}
      </Flex>
      {snapshotMessage && (
        <Text fontSize="xs" color="taupe.500" mt={2}>
          {snapshotMessage}
        </Text>
      )}
    </Box>
  );
}
