import { Box, Flex, Grid, Text } from "@chakra-ui/react";

import type { DashboardHeroDelta, DashboardSummary } from "../../api/portfolio";
import type { ForfaitairBox3Summary } from "../../api/tax";
import type { PeildatumSnapshot } from "../../api/snapshots";
import DisplayMoney from "../portfolio/DisplayMoney";
import Kicker from "../common/Kicker";
import TaxPanelCard from "./TaxPanelCard";
import { formatDateNl, formatEur } from "../../utils/formatMoney";

interface DashboardHeroProps {
  greetingName: string;
  summary: DashboardSummary | null;
  loading: boolean;
  taxYear: number;
  forfaitair: ForfaitairBox3Summary | null;
  peildatum: PeildatumSnapshot | null;
  hasPositions: boolean;
  snapshotBusy: boolean;
  onCreatePeildatum: () => void;
  snapshotMessage?: string;
}

function HeroDelta({ delta }: { delta: DashboardHeroDelta }) {
  if (!delta.available) return null;
  const change = parseFloat(delta.change_eur ?? "0");
  const up = change >= 0;

  return (
    <Flex align="center" gap={6} mt={5} flexWrap="wrap">
      <Flex
        align="center"
        gap={2}
        fontSize="sm"
        sx={{ fontFeatureSettings: '"tnum" 1', fontVariantNumeric: "tabular-nums" }}
        color={up ? "moss.500" : "rust.500"}
        fontWeight={600}
      >
        <Text as="span">{up ? "▲" : "▼"}</Text>
        <Text as="span">{formatEur(delta.change_eur ?? "0")}</Text>
        <Text as="span" opacity={0.9}>
          ({up ? "+" : ""}
          {delta.change_percent}%)
        </Text>
      </Flex>
      <Kicker color="ink.faint" letterSpacing="0.1em">
        afgelopen 30 dagen
      </Kicker>
    </Flex>
  );
}

export default function DashboardHero({
  greetingName,
  summary,
  loading,
  taxYear,
  forfaitair,
  peildatum,
  hasPositions,
  snapshotBusy,
  onCreatePeildatum,
  snapshotMessage,
}: DashboardHeroProps) {
  const todayLabel = formatDateNl(new Date().toISOString());

  return (
    <Grid
      templateColumns={{ base: "1fr", xl: "1.35fr 1fr" }}
      gap={{ base: 6, xl: 10 }}
      py={{ base: 6, md: 10 }}
      px={{ base: 0, md: 0 }}
      borderBottom="1px solid"
      borderColor="line.DEFAULT"
    >
      <Box>
        <Kicker mb={4} letterSpacing="0.2em">
          Welkom terug, {greetingName} —{" "}
          <Box as="span" color="taupe.500">
            {todayLabel}
          </Box>
        </Kicker>

        <Text
          fontFamily="heading"
          fontStyle="italic"
          fontSize="md"
          color="ink.dim"
          mb={2}
        >
          Totaal vermogen, alle platformen
        </Text>

        {loading ? (
          <Text color="ink.dim" fontSize="sm">
            Gegevens laden…
          </Text>
        ) : (
          <>
            <DisplayMoney amount={summary?.total_value_eur ?? "0"} size="hero" />
            {summary?.hero_delta_30d && <HeroDelta delta={summary.hero_delta_30d} />}
          </>
        )}
      </Box>

      <TaxPanelCard
        taxYear={taxYear}
        forfaitair={forfaitair}
        peildatum={peildatum}
        hasPositions={hasPositions}
        snapshotBusy={snapshotBusy}
        onCreatePeildatum={onCreatePeildatum}
        snapshotMessage={snapshotMessage}
      />
    </Grid>
  );
}
