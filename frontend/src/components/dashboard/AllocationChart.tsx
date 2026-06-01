import { Box, Flex, Text, VStack } from "@chakra-ui/react";
import { useState } from "react";
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Sector,
  Tooltip,
} from "recharts";

import type { DashboardCategory } from "../../api/portfolio";
import { formatEur } from "../../utils/formatMoney";
import { CHART_COLORS } from "./chartTheme";

interface AllocationChartProps {
  categories: DashboardCategory[];
  totalLabel?: string;
}

interface SliceRow extends DashboardCategory {
  percent: number;
  color: string;
  name: string;
  value: number;
}

function ActiveSlice(props: {
  cx?: number;
  cy?: number;
  innerRadius?: number;
  outerRadius?: number;
  startAngle?: number;
  endAngle?: number;
  fill?: string;
}) {
  const { cx = 0, cy = 0, innerRadius = 0, outerRadius = 0, startAngle, endAngle, fill } =
    props;
  return (
    <Sector
      cx={cx}
      cy={cy}
      innerRadius={innerRadius}
      outerRadius={outerRadius + 6}
      startAngle={startAngle}
      endAngle={endAngle}
      fill={fill}
      stroke="#FAFAF7"
      strokeWidth={2}
    />
  );
}

function AllocationTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: SliceRow }[];
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <Box
      bg="paper"
      border="1px solid"
      borderColor="line.DEFAULT"
      borderRadius="base"
      px={3}
      py={2}
      boxShadow="md"
      fontSize="sm"
    >
      <Text fontWeight={600}>{row.label}</Text>
      <Text color="ink.dim" mt={0.5}>
        {formatEur(row.value_eur)} · {row.share_percent}%
      </Text>
    </Box>
  );
}

export default function AllocationChart({ categories, totalLabel }: AllocationChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | undefined>(undefined);

  if (categories.length === 0) {
    return (
      <Text fontSize="sm" color="ink.dim">
        Geen verdeling beschikbaar.
      </Text>
    );
  }

  const segments: SliceRow[] = categories.map((cat, index) => ({
    ...cat,
    name: cat.label,
    percent: Math.max(0, parseFloat(cat.share_percent) || 0),
    value: parseFloat(cat.value_eur) || 0,
    color: CHART_COLORS[index % CHART_COLORS.length],
  }));

  return (
    <Flex gap={4} align="center" flexWrap={{ base: "wrap", md: "nowrap" }}>
      <Box flex="0 0 160px" h="160px" w="160px" position="relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={segments}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={48}
              outerRadius={68}
              paddingAngle={2}
              activeIndex={activeIndex}
              activeShape={ActiveSlice}
              onMouseEnter={(_, index) => setActiveIndex(index)}
              onMouseLeave={() => setActiveIndex(undefined)}
            >
              {segments.map((seg) => (
                <Cell key={seg.label} fill={seg.color} stroke="transparent" />
              ))}
            </Pie>
            <Tooltip content={<AllocationTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        <Box
          position="absolute"
          inset="0"
          display="flex"
          alignItems="center"
          justifyContent="center"
          pointerEvents="none"
          textAlign="center"
          px={3}
        >
          <Text fontSize="xs" color="ink.dim" lineHeight={1.35}>
            {totalLabel ?? "Totaal"}
          </Text>
        </Box>
      </Box>
      <VStack align="stretch" spacing={1.5} flex={1} minW="140px">
        {segments.map((seg) => (
          <Flex
            key={seg.label}
            align="center"
            gap={2}
            fontSize="sm"
            py={0.5}
            px={1}
            borderRadius="sm"
            cursor="default"
            _hover={{ bg: "azure.50" }}
            onMouseEnter={() => setActiveIndex(segments.indexOf(seg))}
            onMouseLeave={() => setActiveIndex(undefined)}
          >
            <Box w={2.5} h={2.5} borderRadius="sm" bg={seg.color} flexShrink={0} />
            <Text flex={1} color="ink.dim" noOfLines={1}>
              {seg.label}
            </Text>
            <Text fontWeight={500} fontSize="sm">
              {formatEur(seg.value_eur)}
            </Text>
            <Text color="taupe.500" fontSize="xs" minW="36px" textAlign="right">
              {seg.share_percent}%
            </Text>
          </Flex>
        ))}
      </VStack>
    </Flex>
  );
}
