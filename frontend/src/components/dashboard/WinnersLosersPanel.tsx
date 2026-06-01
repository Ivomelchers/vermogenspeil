import { Box, Button, Flex, HStack, Text, VStack } from "@chakra-ui/react";
import { useState } from "react";

import type { DashboardMover, DashboardMoversByPeriod } from "../../api/portfolio";
import DisplayMoney from "../portfolio/DisplayMoney";
import Kicker from "../common/Kicker";

const PERIOD_LABELS: Record<string, string> = {
  day: "Vandaag",
  week: "Week",
  month: "Maand",
  ytd: "YTD",
};

type PeriodKey = keyof DashboardMoversByPeriod;

interface WinnersLosersPanelProps {
  movers: DashboardMoversByPeriod;
}

function MoverRow({ item, tone }: { item: DashboardMover; tone: "positive" | "negative" }) {
  const pct = parseFloat(item.change_percent);
  return (
    <Flex justify="space-between" align="center" py={2} px={2} borderRadius="base" _hover={{ bg: "azure.50" }}>
      <Box>
        <Text fontSize="sm" fontWeight={600} color="ink.primary">
          {item.symbol}
        </Text>
        <Text fontSize="xs" color="taupe.500" noOfLines={1}>
          {item.name}
        </Text>
      </Box>
      <Box textAlign="right">
        <DisplayMoney amount={item.change_eur} size="sm" signed tone={tone} />
        <Text fontSize="xs" color={pct >= 0 ? "moss.500" : "rust.500"}>
          {pct >= 0 ? "+" : ""}
          {item.change_percent}%
        </Text>
      </Box>
    </Flex>
  );
}

function MoverList({
  title,
  items,
  emptyLabel,
  tone,
}: {
  title: string;
  items: DashboardMover[];
  emptyLabel: string;
  tone: "positive" | "negative";
}) {
  return (
    <Box flex={1} minW={0}>
      <Kicker mb={2}>{title}</Kicker>
      {items.length === 0 ? (
        <Text fontSize="sm" color="ink.dim">
          {emptyLabel}
        </Text>
      ) : (
        <VStack align="stretch" spacing={0}>
          {items.map((item) => (
            <MoverRow key={`${item.symbol}-${item.position_id}`} item={item} tone={tone} />
          ))}
        </VStack>
      )}
    </Box>
  );
}

export default function WinnersLosersPanel({ movers }: WinnersLosersPanelProps) {
  const periods = (Object.keys(PERIOD_LABELS) as PeriodKey[]).filter((p) => movers[p]);
  const [period, setPeriod] = useState<PeriodKey>(periods.includes("month") ? "month" : periods[0] ?? "month");

  const data = movers[period];
  if (!data) {
    return (
      <Text fontSize="sm" color="ink.dim">
        Onvoldoende data voor winnaars en verliezers.
      </Text>
    );
  }

  return (
    <Box>
      <HStack spacing={1} mb={3} flexWrap="wrap">
        {periods.map((key) => (
          <Button
            key={key}
            size="xs"
            variant={period === key ? "fiscal" : "ghost"}
            onClick={() => setPeriod(key)}
          >
            {PERIOD_LABELS[key]}
          </Button>
        ))}
      </HStack>
      <Flex gap={4} direction={{ base: "column", md: "row" }}>
        <MoverList
          title="Stijgers"
          items={data.gainers}
          emptyLabel="Geen stijgers in deze periode."
          tone="positive"
        />
        <MoverList
          title="Dalers"
          items={data.losers}
          emptyLabel="Geen dalers in deze periode."
          tone="negative"
        />
      </Flex>
    </Box>
  );
}
