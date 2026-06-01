import { useEffect, useState } from "react";
import { Box, Button, Grid, Link, Text, VStack } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import { getDashboardSummary, type DashboardSummary } from "../api/portfolio";
import AuthAlert from "../components/auth/AuthAlert";
import DisplayMoney from "../components/portfolio/DisplayMoney";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import MoneyText from "../components/common/MoneyText";
import { useUser } from "../contexts/UserContext";
import { formatDateNl, formatEur } from "../utils/formatMoney";
import { getApiErrorMessage } from "../utils/apiError";

export default function DashboardPage() {
  const { user } = useUser();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    void loadSummary();
  }, []);

  async function loadSummary() {
    setLoading(true);
    setError("");
    try {
      const data = await getDashboardSummary();
      setSummary(data);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Dashboard laden mislukt."));
    } finally {
      setLoading(false);
    }
  }

  const greetingName = user?.first_name || user?.email.split("@")[0] || "daar";
  const todayLabel = formatDateNl(new Date().toISOString());
  const totalValue = summary?.total_value_eur ?? "0";
  const hasPositions = (summary?.positions_count ?? 0) > 0;

  return (
    <VStack align="stretch" spacing={8}>
      {error && <AuthAlert tone="error">{error}</AuthAlert>}

      <Grid
        templateColumns={{ base: "1fr", xl: "1.3fr 1fr" }}
        gap={12}
        pb={8}
        borderBottom="1px solid"
        borderColor="line.DEFAULT"
      >
        <Box>
          <Kicker mb={4}>
            Overzicht · <Box as="span" color="taupe.500">{todayLabel}</Box>
          </Kicker>
          <Text
            fontFamily="heading"
            fontStyle="italic"
            fontSize="15px"
            color="ink.dim"
            mb={1.5}
          >
            Welkom terug, {greetingName} — totaal vermogen
          </Text>

          {loading ? (
            <Text color="ink.dim" fontSize="sm">
              Gegevens laden…
            </Text>
          ) : (
            <>
              <DisplayMoney amount={totalValue} />
              <Kicker mt={3} mb={4}>
                {summary?.valuation_note ?? "Kostprijs — marktwaarden volgen in fase 5"}
              </Kicker>
              {summary?.returns && parseFloat(summary.returns.invested_eur) > 0 ? (
                <Box display="flex" gap={6} flexWrap="wrap" alignItems="center">
                  <MoneyText
                    variant="delta"
                    tone={
                      parseFloat(summary.returns.unrealized_return_eur) >= 0
                        ? "positive"
                        : "negative"
                    }
                  >
                    {parseFloat(summary.returns.unrealized_return_eur) >= 0 ? "+ " : "− "}
                    {formatEur(Math.abs(parseFloat(summary.returns.unrealized_return_eur)))}
                  </MoneyText>
                  <Kicker>
                    {summary.returns.unrealized_return_percent}% · t.o.v. inleg (kostprijs)
                  </Kicker>
                </Box>
              ) : (
                <Kicker>Laad demo-data om rendement te zien</Kicker>
              )}
            </>
          )}
        </Box>

        <FiscalCard p={6}>
          <Kicker mb={3}>Belastingjaar {user?.active_tax_year ?? "—"} · Peildatum 1 jan</Kicker>
          <Text fontFamily="heading" fontStyle="italic" fontSize="15px" color="ink.dim" mb={2}>
            Te betalen belasting
          </Text>
          <MoneyText variant="display" fontSize={{ base: "48px", md: "56px" }} color="ink.dim">
            —
          </MoneyText>
          <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.6}>
            {hasPositions
              ? `Grondslag (kostprijs): ${formatEur(totalValue)}. Box 3-berekening volgt in fase 6.`
              : "Koppel platformen of laad voorbeelddata om uw vermogen te zien."}
          </Text>
        </FiscalCard>
      </Grid>

      {!loading && !hasPositions && (
        <FiscalCard p={6}>
          <Text fontFamily="heading" fontStyle="italic" color="ink.dim" lineHeight={1.7} mb={4}>
            Nog geen posities in uw portefeuille. Laad lokaal voorbeelddata of koppel een platform.
          </Text>
          <Button as={RouterLink} to="/platforms" variant="fiscal" size="sm">
            Naar Mijn platformen
          </Button>
        </FiscalCard>
      )}

      {hasPositions && summary && (
        <>
          <Grid
            templateColumns={{
              base: "1fr",
              md: `repeat(${Math.min(summary.by_category.length, 4)}, 1fr)`,
            }}
            gap={4}
          >
            {summary.by_category.map((category) => (
              <InsightCard
                key={category.label}
                label={category.label}
                value={formatEur(category.value_eur)}
                delta={`${category.share_percent}% van totaal`}
                tone="accent"
              />
            ))}
          </Grid>

          <Grid templateColumns={{ base: "1fr", xl: "1.2fr 1fr" }} gap={6}>
            <Box>
              <Kicker mb={3}>Posities · {summary.positions_count}</Kicker>
              <VStack align="stretch" spacing={2}>
                {summary.positions.slice(0, 6).map((position) => (
                  <FiscalCard key={position.id} p={4}>
                    <Box display="flex" justifyContent="space-between" gap={4} flexWrap="wrap">
                      <Box>
                        <Text fontWeight={600}>{position.symbol}</Text>
                        <Kicker>{position.category_label}</Kicker>
                      </Box>
                      <Box textAlign="right">
                        <Text fontWeight={500}>{formatEur(position.value_eur)}</Text>
                        <Text fontSize="sm" color="ink.dim">
                          {position.quantity} st.
                        </Text>
                      </Box>
                    </Box>
                  </FiscalCard>
                ))}
              </VStack>
              {summary.positions.length > 6 && (
                <Button
                  as={RouterLink}
                  to="/portfolio"
                  variant="fiscalOutline"
                  size="sm"
                  mt={3}
                >
                  Alle posities bekijken
                </Button>
              )}
            </Box>

            <Box>
              <Kicker mb={3}>
                Platformen · {summary.platforms.length} actief
              </Kicker>
              {summary.platforms.length === 0 ? (
                <FiscalCard p={4}>
                  <Text fontSize="sm" color="ink.dim" lineHeight={1.6}>
                    Geen gekoppelde platformen.{" "}
                    <Link as={RouterLink} to="/platforms" color="azure.500">
                      Platform toevoegen
                    </Link>
                  </Text>
                </FiscalCard>
              ) : (
                <VStack align="stretch" spacing={2}>
                  {summary.platforms.map((platform) => (
                    <FiscalCard key={platform.id} p={4}>
                      <Text fontWeight={600}>
                        {platform.display_name}
                        {platform.is_demo && (
                          <Text as="span" fontSize="xs" color="gold.600" ml={2}>
                            demo
                          </Text>
                        )}
                      </Text>
                      <Kicker>
                        {platform.connection_method_display} · {platform.platform_display}
                      </Kicker>
                    </FiscalCard>
                  ))}
                </VStack>
              )}
            </Box>
          </Grid>
        </>
      )}
    </VStack>
  );
}

function InsightCard({
  label,
  value,
  delta,
  tone,
}: {
  label: string;
  value: string;
  delta: string;
  tone: "positive" | "negative" | "accent";
}) {
  const valueTone = tone === "positive" ? "positive" : tone === "negative" ? "negative" : "default";
  const deltaTone = tone === "accent" ? "default" : valueTone;

  return (
    <FiscalCard p={5}>
      <Kicker mb={3}>{label}</Kicker>
      <MoneyText
        fontFamily="heading"
        fontSize="32px"
        letterSpacing="-0.02em"
        tone={valueTone === "default" ? "accent" : valueTone}
        mb={2}
      >
        {value}
      </MoneyText>
      <MoneyText variant="delta" tone={deltaTone} color={deltaTone === "default" ? "ink.dim" : undefined}>
        {delta}
      </MoneyText>
    </FiscalCard>
  );
}
