import { Box, Flex, Grid, Text } from "@chakra-ui/react";
import { useState } from "react";

import type { DashboardMover, DashboardMoversByPeriod } from "../../api/portfolio";
import Kicker from "../common/Kicker";
import { formatEur } from "../../utils/formatMoney";

const PERIOD_LABELS: Record<string, string> = {
  day: "Vandaag",
  week: "Deze week",
  month: "Deze maand",
  ytd: "Boekjaar",
};

type PeriodKey = keyof DashboardMoversByPeriod;

function MoverRow({ item, up }: { item: DashboardMover; up: boolean }) {
  return (
    <Grid
      templateColumns="1fr auto auto"
      gap={4}
      alignItems="baseline"
      py={2.5}
      borderBottom="1px solid"
      borderColor="line.soft"
      _last={{ borderBottom: "none" }}
    >
      <Box minW={0}>
        <Text fontSize="sm" fontWeight={500} color="ink.primary">
          {item.name}
        </Text>
        <Text
          as="span"
          fontSize="10px"
          color="ink.faint"
          ml={2}
          sx={{ fontFeatureSettings: '"tnum" 1', fontVariantNumeric: "tabular-nums" }}
        >
          {item.symbol}
        </Text>
      </Box>
      <Text
        fontSize="sm"
        textAlign="right"
        color={up ? "moss.500" : "rust.500"}
        sx={{ fontFeatureSettings: '"tnum" 1', fontVariantNumeric: "tabular-nums" }}
      >
        {up ? "+" : ""}
        {formatEur(item.change_eur)}
      </Text>
      <Text
        fontSize="11px"
        px={2}
        py={0.5}
        borderRadius="sm"
        textAlign="center"
        minW="62px"
        color={up ? "moss.500" : "rust.500"}
        bg={up ? "moss.50" : "rust.50"}
        sx={{ fontFeatureSettings: '"tnum" 1', fontVariantNumeric: "tabular-nums" }}
      >
        {up ? "+" : ""}
        {item.change_percent}%
      </Text>
    </Grid>
  );
}

function MoversColumn({
  title,
  dotColor,
  items,
  emptyLabel,
  up,
}: {
  title: string;
  dotColor: string;
  items: DashboardMover[];
  emptyLabel: string;
  up: boolean;
}) {
  return (
    <Box px={{ base: 4, md: 7 }} py={5}>
      <Flex align="center" gap={2} mb={4}>
        <Box w="6px" h="6px" borderRadius="full" bg={dotColor} />
        <Kicker letterSpacing="0.18em">{title}</Kicker>
      </Flex>
      {items.length === 0 ? (
        <Text fontSize="sm" color="ink.dim">
          {emptyLabel}
        </Text>
      ) : (
        items.map((item) => (
          <MoverRow key={`${item.symbol}-${item.position_id}`} item={item} up={up} />
        ))
      )}
    </Box>
  );
}

interface WinnersLosersPanelProps {
  movers: DashboardMoversByPeriod;
}

export default function WinnersLosersPanel({ movers }: WinnersLosersPanelProps) {
  const periods = (Object.keys(PERIOD_LABELS) as PeriodKey[]).filter((p) => movers[p]);
  const [period, setPeriod] = useState<PeriodKey>(
    periods.includes("month") ? "month" : periods[0] ?? "month",
  );

  const data = movers[period];
  if (!data) {
    return (
      <Text fontSize="sm" color="ink.dim">
        Onvoldoende data voor winnaars en verliezers.
      </Text>
    );
  }

  return (
    <Box
      bg="backgroundCard"
      border="1px solid"
      borderColor="line.DEFAULT"
      borderRadius="base"
      overflow="hidden"
    >
      <Flex borderBottom="1px solid" borderColor="line.soft" bg="backgroundHover">
        {periods.map((key) => (
          <Box
            key={key}
            as="button"
            type="button"
            flex={1}
            py={3.5}
            px={2}
            textAlign="center"
            border="none"
            borderBottom="2px solid"
            borderBottomColor={period === key ? "azure.500" : "transparent"}
            bg={period === key ? "backgroundCard" : "transparent"}
            color={period === key ? "azure.500" : "ink.faint"}
            fontSize="10px"
            letterSpacing="0.15em"
            textTransform="uppercase"
            fontWeight={period === key ? 600 : 400}
            cursor="pointer"
            transition="all 0.15s ease"
            _hover={{ color: period === key ? "azure.500" : "ink.dim" }}
            onClick={() => setPeriod(key)}
          >
            {PERIOD_LABELS[key]}
          </Box>
        ))}
      </Flex>

      <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }}>
        <Box borderRight={{ md: "1px solid" }} borderColor={{ md: "line.soft" }}>
          <MoversColumn
            title="Winnaars"
            dotColor="moss.500"
            items={data.gainers}
            emptyLabel="Geen stijgers in deze periode."
            up
          />
        </Box>
        <MoversColumn
          title="Verliezers"
          dotColor="rust.500"
          items={data.losers}
          emptyLabel="Geen dalers in deze periode."
          up={false}
        />
      </Grid>
    </Box>
  );
}
