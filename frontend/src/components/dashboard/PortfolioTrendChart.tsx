import { Box, Text } from "@chakra-ui/react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DashboardValuePoint } from "../../api/portfolio";
import { formatDateNl, formatEur } from "../../utils/formatMoney";
import { CHART_AXIS, CHART_GRID } from "./chartTheme";

interface PortfolioTrendChartProps {
  points: DashboardValuePoint[];
  valuationNote?: string;
}

function shortMonthLabel(isoDate: string): string {
  const d = new Date(isoDate);
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString("nl-NL", { month: "short", day: "numeric" });
}

interface TooltipPayload {
  value?: number;
  payload?: DashboardValuePoint & { label: string };
}

function TrendTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  if (!row) return null;

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
      <Text fontWeight={600} color="ink.primary">
        {formatEur(String(row.value_eur))}
      </Text>
      <Text fontSize="xs" color="taupe.500" mt={0.5}>
        {formatDateNl(row.date)}
        {row.method === "current"
          ? " · huidige waardering"
          : row.method === "ytd_start"
            ? " · startwaarde dit jaar"
            : " · kostprijs"}
      </Text>
    </Box>
  );
}

export default function PortfolioTrendChart({
  points,
  valuationNote,
}: PortfolioTrendChartProps) {
  if (points.length === 0) {
    return (
      <Text fontSize="sm" color="ink.dim" lineHeight={1.6}>
        Nog geen vermogensdata om een verloop te tonen.
      </Text>
    );
  }

  const data = points.map((p) => ({
    ...p,
    label: shortMonthLabel(p.date),
    value: parseFloat(p.value_eur) || 0,
  }));

  const values = data.map((d) => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = Math.max((max - min) * 0.08, max * 0.02, 1);

  return (
    <Box>
      <Box h="200px" w="100%" mt={1}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="vermogenFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#1E3A5F" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#1E3A5F" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: CHART_AXIS, fontSize: 11 }}
              axisLine={{ stroke: CHART_GRID }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: CHART_AXIS, fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={56}
              tickFormatter={(v: number) =>
                v >= 1000 ? `€${Math.round(v / 1000)}k` : `€${v}`
              }
              domain={[min - padding, max + padding]}
            />
            <Tooltip content={<TrendTooltip />} cursor={{ stroke: "#1E3A5F", strokeWidth: 1 }} />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#1E3A5F"
              strokeWidth={2}
              fill="url(#vermogenFill)"
              dot={{ r: 3, fill: "#1E3A5F", stroke: "#FAFAF7", strokeWidth: 2 }}
              activeDot={{ r: 5, fill: "#1E3A5F", stroke: "#B8934E", strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </Box>
      {valuationNote && (
        <Text fontSize="xs" color="taupe.500" mt={2} lineHeight={1.5}>
          Maandpunten op kostprijs; laatste punt: {valuationNote.toLowerCase()}
        </Text>
      )}
    </Box>
  );
}
