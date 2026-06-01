import { useEffect, useState } from "react";
import { Box, Button, Grid, Link, Text, VStack } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import { getDashboardSummary, type DashboardSummary } from "../api/portfolio";
import {
  createPeildatumSnapshot,
  getPeildatumSnapshot,
  type PeildatumSnapshot,
} from "../api/snapshots";
import AuthAlert from "../components/auth/AuthAlert";
import DisplayMoney from "../components/portfolio/DisplayMoney";
import FiscalCard from "../components/common/FiscalCard";
import Kicker from "../components/common/Kicker";
import MoneyText from "../components/common/MoneyText";
import { useUser } from "../contexts/UserContext";
import { formatDateNl, formatEur } from "../utils/formatMoney";
import { getApiErrorMessage } from "../utils/apiError";
import {
  positionPriceHint,
  returnBasisLabel,
  valuationBasisLabel,
} from "../utils/valuationLabels";

export default function DashboardPage() {
  const { user } = useUser();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [peildatum, setPeildatum] = useState<PeildatumSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [snapshotBusy, setSnapshotBusy] = useState(false);
  const [error, setError] = useState("");
  const [snapshotMessage, setSnapshotMessage] = useState("");

  const taxYear = user?.active_tax_year ?? new Date().getFullYear();

  useEffect(() => {
    void loadSummary();
  }, [taxYear]);

  async function loadSummary() {
    setLoading(true);
    setError("");
    setSnapshotMessage("");
    try {
      const data = await getDashboardSummary();
      setSummary(data);
      const snap = await getPeildatumSnapshot(taxYear);
      setPeildatum(snap);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Dashboard laden mislukt."));
    } finally {
      setLoading(false);
    }
  }

  async function handleCreatePeildatum() {
    setSnapshotBusy(true);
    setSnapshotMessage("");
    try {
      const snap = await createPeildatumSnapshot(taxYear);
      setPeildatum(snap);
      setSnapshotMessage(`Peildatum ${taxYear} vastgelegd.`);
    } catch (createError) {
      setSnapshotMessage(
        getApiErrorMessage(createError, "Peildatum vastleggen mislukt."),
      );
    } finally {
      setSnapshotBusy(false);
    }
  }

  const greetingName = user?.first_name || user?.email.split("@")[0] || "daar";
  const todayLabel = formatDateNl(new Date().toISOString());
  const totalValue = summary?.total_value_eur ?? "0";
  const hasPositions = (summary?.positions_count ?? 0) > 0;
  const basisLabel = valuationBasisLabel(summary?.valuation_method);

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
            Welkom terug, {greetingName} — totaal vermogen ({basisLabel.toLowerCase()})
          </Text>

          {loading ? (
            <Text color="ink.dim" fontSize="sm">
              Gegevens laden…
            </Text>
          ) : (
            <>
              <DisplayMoney amount={totalValue} />
              <Kicker mt={3} mb={4}>
                {summary?.valuation_note ??
                  "Waarde op basis van kostprijs — geen live koersen beschikbaar."}
              </Kicker>
              {summary?.returns && parseFloat(summary.returns.invested_eur) > 0 ? (
                <Box display="flex" gap={6} flexWrap="wrap" alignItems="baseline">
                  <DisplayMoney
                    amount={summary.returns.unrealized_return_eur}
                    size="sm"
                    signed
                    tone={
                      parseFloat(summary.returns.unrealized_return_eur) >= 0
                        ? "positive"
                        : "negative"
                    }
                  />
                  <Kicker>
                    {summary.returns.unrealized_return_percent}% ·{" "}
                    {returnBasisLabel(summary.returns.method)}
                  </Kicker>
                  {summary.returns.note && (
                    <Text fontSize="xs" color="ink.dim" width="100%">
                      {summary.returns.note}
                    </Text>
                  )}
                </Box>
              ) : hasPositions ? (
                <Kicker>Voeg transacties toe om rendement te berekenen</Kicker>
              ) : null}
              {summary?.ytd?.available && (
                <Box mt={4} pt={3} borderTop="1px solid" borderColor="line.soft">
                  <Kicker mb={1}>YTD {summary.ytd.year}</Kicker>
                  <DisplayMoney
                    amount={summary.ytd.ytd_return_eur ?? "0"}
                    size="sm"
                    signed
                    tone={
                      parseFloat(summary.ytd.ytd_return_eur ?? "0") >= 0
                        ? "positive"
                        : "negative"
                    }
                  />
                  <Kicker>
                    {summary.ytd.ytd_return_percent}% · t.o.v.{" "}
                    {formatEur(summary.ytd.start_value_eur ?? "0")} begin {summary.ytd.year}
                  </Kicker>
                </Box>
              )}
            </>
          )}
        </Box>

        <FiscalCard p={6}>
          <Kicker mb={3}>Belastingjaar {taxYear} · Peildatum 1 jan</Kicker>
          <Text fontFamily="heading" fontStyle="italic" fontSize="15px" color="ink.dim" mb={2}>
            {peildatum ? "Vastgelegd vermogen peildatum" : "Te betalen belasting"}
          </Text>
          {peildatum ? (
            <>
              <DisplayMoney amount={peildatum.total_value_eur} size="md" />
              <Kicker mt={2} mb={2}>
                Vastgelegd op {formatDateNl(peildatum.data.captured_at)} ·{" "}
                {valuationBasisLabel(peildatum.valuation_method).toLowerCase()}
              </Kicker>
            </>
          ) : (
            <MoneyText variant="display" fontSize={{ base: "48px", md: "56px" }} color="ink.dim">
              —
            </MoneyText>
          )}
          <Text color="ink.dim" fontSize="sm" mt={3} lineHeight={1.6}>
            {peildatum
              ? `Peildatum ${formatDateNl(peildatum.peildatum)} (CET). Box 3-berekening volgt in fase 6.`
              : hasPositions
                ? `Nog geen snapshot voor ${taxYear}. Huidig vermogen (${basisLabel.toLowerCase()}): ${formatEur(totalValue)}.`
                : "Koppel een platform of voeg handmatig assets toe om uw vermogen te zien."}
          </Text>
          {hasPositions && !peildatum && (
            <Button
              variant="fiscalOutline"
              size="sm"
              mt={4}
              isLoading={snapshotBusy}
              onClick={() => void handleCreatePeildatum()}
            >
              Peildatum {taxYear} vastleggen
            </Button>
          )}
          {snapshotMessage && (
            <Text fontSize="xs" color="taupe.500" mt={2}>
              {snapshotMessage}
            </Text>
          )}
        </FiscalCard>
      </Grid>

      {!loading && !hasPositions && (
        <FiscalCard p={6}>
          <Text fontFamily="heading" fontStyle="italic" color="ink.dim" lineHeight={1.7} mb={4}>
            Nog geen posities in uw portefeuille. Koppel een broker of voeg handmatig assets en
            transacties toe.
          </Text>
          <Box display="flex" gap={2} flexWrap="wrap" mt={2}>
            <Button as={RouterLink} to="/platforms" variant="fiscal" size="sm">
              Platform koppelen
            </Button>
            <Button as={RouterLink} to="/portfolio/manual/asset" variant="fiscalOutline" size="sm">
              Asset toevoegen
            </Button>
          </Box>
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
                {summary.positions.slice(0, 6).map((position) => {
                  const priceHint = positionPriceHint(position);
                  return (
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
                          {priceHint && (
                            <Text fontSize="xs" color="taupe.500" mt={0.5}>
                              {priceHint}
                            </Text>
                          )}
                        </Box>
                      </Box>
                    </FiscalCard>
                  );
                })}
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
