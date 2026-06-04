import { Box, Text } from "@chakra-ui/react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DashboardValuePoint } from "../../api/portfolio";
import { formatEur } from "../../utils/formatMoney";
import { CHART_AXIS, CHART_GRID } from "./chartTheme";

interface PortfolioTrendChartProps {
  points: DashboardValuePoint[];
}

function shortMonthLabel(isoDate: string): string {
  const d = new Date(isoDate);
  if (Number.isNaN(d.getTime())) return isoDate;
  return d.toLocaleDateString("nl-NL", { month: "short", day: "numeric" });
}

interface TooltipPayload {
  payload?: {
    label: string;
    portfolio: number;
    costBasis: number;
  };
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
      <Text fontSize="xs" color="taupe.500" mb={1}>
        {row.label}
      </Text>
      <Text color="ink.primary">
        Waarde: {formatEur(String(row.portfolio))}
      </Text>
      <Text color="taupe.600">
        Inleg: {formatEur(String(row.costBasis))}
      </Text>
    </Box>
  );
}

export default function PortfolioTrendChart({ points }: PortfolioTrendChartProps) {
  if (points.length === 0) {
    return (
      <Text fontSize="sm" color="ink.dim" lineHeight={1.6}>
        Nog geen vermogensdata om een verloop te tonen.
      </Text>
    );
  }

  const data = points.map((p) => ({
    label: shortMonthLabel(p.date),
    portfolio: parseFloat(p.value_eur) || 0,
    costBasis: parseFloat(p.cost_basis_eur ?? p.value_eur) || 0,
  }));

  const allValues = data.flatMap((d) => [d.portfolio, d.costBasis]);
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const padding = Math.max((max - min) * 0.08, max * 0.02, 1);

  return (
    <Box>
      <Box h="220px" w="100%" mt={1}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
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
            <Tooltip content={<TrendTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
              formatter={(value) => (value === "portfolio" ? "Waarde" : "Inleg (kostprijs)")}
            />
            <Line
              type="monotone"
              dataKey="portfolio"
              name="portfolio"
              stroke="#1E3A5F"
              strokeWidth={2}
              dot={{ r: 2, fill: "#1E3A5F" }}
              activeDot={{ r: 4 }}
            />
            <Line
              type="monotone"
              dataKey="costBasis"
              name="costBasis"
              stroke="#B8934E"
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Box>
  );
}
