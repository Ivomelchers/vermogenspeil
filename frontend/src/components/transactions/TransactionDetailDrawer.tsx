import type { ReactNode } from "react";
import { useMemo } from "react";
import {
  Box,
  Divider,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Flex,
  Grid,
  Link,
  Spinner,
  Text,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";

import type { Transaction } from "../../api/portfolio";
import { getLiveQuotes } from "../../api/pricing";
import { formatDateNl, formatDateTimeNl, formatEur, formatSmartEur } from "../../utils/formatMoney";
import { formatQuantity } from "../../utils/formatQuantity";
import { platformLabel } from "../../utils/platformLabels";
import {
  ASSET_TYPE_LABELS,
  FISCAL_CATEGORY_LABELS,
  transactionTypeLabel,
} from "../../utils/transactionLabels";
import TransactionTypeBadge from "./TransactionTypeBadge";

interface TransactionDetailDrawerProps {
  transaction: Transaction | null;
  isOpen: boolean;
  onClose: () => void;
}

const LIVE_PRICE_ASSET_TYPES = new Set(["stock", "etf", "fund", "crypto", "metal"]);

function isTradeTransaction(type: string): boolean {
  return type === "buy" || type === "sell";
}

function exportSectionTitle(type: string): string {
  switch (type) {
    case "dividend":
      return "Dividend (uit export)";
    case "fee":
      return "Kosten (uit export)";
    case "deposit":
      return "Storting (uit export)";
    case "withdrawal":
      return "Opname (uit export)";
    default:
      return "Transactie (uit export)";
  }
}

function unitAmountLabel(type: string): string {
  switch (type) {
    case "dividend":
      return "Dividend per stuk";
    case "buy":
    case "sell":
      return "Koers bij transactie";
    default:
      return "Bedrag per stuk";
  }
}

function quantityLabel(type: string): string {
  return type === "dividend" ? "Aantal stuks (bij uitkering)" : "Aantal";
}

function DetailRow({
  label,
  value,
  mono,
  highlight,
}: {
  label: string;
  value: ReactNode;
  mono?: boolean;
  highlight?: boolean;
}) {
  return (
    <Flex justify="space-between" align="flex-start" gap={4} py={2.5}>
      <Text fontSize="sm" color="ink.dim" flexShrink={0}>
        {label}
      </Text>
      <Text
        fontSize="sm"
        color={highlight ? "moss.600" : "ink.primary"}
        textAlign="right"
        fontWeight={highlight ? 600 : 500}
        fontFamily={mono ? "mono" : undefined}
        wordBreak="break-word"
      >
        {value}
      </Text>
    </Flex>
  );
}

function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <Text
      fontSize="10px"
      letterSpacing="0.14em"
      textTransform="uppercase"
      color="ink.faint"
      fontWeight={600}
      mb={1}
    >
      {children}
    </Text>
  );
}

function formatLiveFetchedAt(iso: string): string {
  return new Date(iso).toLocaleString("nl-NL", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function livePriceSourceLabel(source: string): string {
  if (source === "yahoo") return "Yahoo Finance";
  if (source === "bitvavo") return "Bitvavo";
  if (source === "coingecko") return "CoinGecko";
  return source;
}

export default function TransactionDetailDrawer({
  transaction,
  isOpen,
  onClose,
}: TransactionDetailDrawerProps) {
  const tx = transaction;
  const canFetchLive = Boolean(
    tx &&
      isOpen &&
      tx.asset.symbol !== "EUR" &&
      tx.asset.asset_type !== "cash" &&
      LIVE_PRICE_ASSET_TYPES.has(tx.asset.asset_type),
  );

  const { data: liveQuotes, isLoading: liveLoading } = useQuery({
    queryKey: ["live-quote", tx?.asset.symbol, tx?.asset.asset_type],
    queryFn: () => getLiveQuotes([tx!.asset.symbol], tx!.asset.asset_type),
    enabled: canFetchLive,
    staleTime: 60_000,
  });

  const liveQuote = liveQuotes?.[0];

  const priceDelta = useMemo(() => {
    if (!tx || !isTradeTransaction(tx.transaction_type)) return null;
    if (!tx.price_eur || !liveQuote?.price_eur) return null;
    const txPrice = parseFloat(tx.price_eur);
    const live = parseFloat(liveQuote.price_eur);
    if (!Number.isFinite(txPrice) || txPrice <= 0 || !Number.isFinite(live)) return null;
    return ((live - txPrice) / txPrice) * 100;
  }, [tx, liveQuote?.price_eur]);

  const priceDeltaLabel = useMemo(() => {
    if (priceDelta === null) return null;
    const abs = Math.abs(priceDelta).toFixed(1).replace(".", ",");
    if (priceDelta >= 0) return `${abs}% boven uw transactiekoers`;
    return `${abs}% onder uw transactiekoers`;
  }, [priceDelta]);

  if (!tx) {
    return null;
  }

  const total = tx.total_eur ? parseFloat(tx.total_eur) : null;
  const fee = parseFloat(tx.fee_eur || "0");
  const isOutflow =
    tx.transaction_type === "buy" ||
    tx.transaction_type === "withdrawal" ||
    tx.transaction_type === "fee" ||
    (total !== null && total < 0);

  const importHref = tx.import_batch_id
    ? `/transactions?import_batch_id=${tx.import_batch_id}`
    : null;

  return (
    <Drawer isOpen={isOpen} placement="right" onClose={onClose} size="md">
      <DrawerOverlay bg="blackAlpha.300" backdropFilter="blur(2px)" />
      <DrawerContent bg="background" boxShadow="2xl">
        <DrawerCloseButton top={4} right={4} />
        <DrawerHeader pt={8} pb={4} borderBottom="1px solid" borderColor="line.soft">
          <Flex align="center" gap={2} mb={3}>
            <TransactionTypeBadge type={tx.transaction_type} />
            <Text fontSize="xs" color="ink.faint">
              #{tx.id}
            </Text>
          </Flex>
          <Text fontFamily="heading" fontSize="2xl" fontWeight={400} lineHeight={1.2}>
            {tx.asset.name !== tx.asset.symbol ? tx.asset.name : tx.asset.symbol}
          </Text>
          <Text fontSize="sm" color="ink.dim" mt={1}>
            {formatDateTimeNl(tx.occurred_at)}
          </Text>
          {total !== null && (
            <Text
              fontFamily="heading"
              fontSize="3xl"
              fontWeight={500}
              mt={4}
              color={isOutflow ? "ink.primary" : "moss.600"}
              sx={{ fontFeatureSettings: '"tnum" 1' }}
            >
              {formatEur(total)}
            </Text>
          )}
        </DrawerHeader>

        <DrawerBody py={6}>
          <Box mb={6}>
            <SectionTitle>Belegging</SectionTitle>
            <Box bg="paper" border="1px solid" borderColor="line.soft" borderRadius="md" px={4}>
              <DetailRow label="Symbool" value={tx.asset.symbol} mono />
              <Divider borderColor="line.soft" />
              <DetailRow label="Naam" value={tx.asset.name} />
              <Divider borderColor="line.soft" />
              <DetailRow
                label="Type asset"
                value={ASSET_TYPE_LABELS[tx.asset.asset_type] ?? tx.asset.asset_type}
              />
              <Divider borderColor="line.soft" />
              <DetailRow
                label="Box 3-categorie"
                value={FISCAL_CATEGORY_LABELS[tx.asset.category] ?? tx.asset.category}
              />
            </Box>
          </Box>

          {canFetchLive && (
            <Box mb={6}>
              <SectionTitle>Markt nu</SectionTitle>
              <Box
                bg="azure.50"
                border="1px solid"
                borderColor="azure.100"
                borderRadius="md"
                px={4}
              >
                {liveLoading ? (
                  <Flex py={4} justify="center" align="center" gap={2}>
                    <Spinner size="sm" color="azure.500" />
                    <Text fontSize="sm" color="ink.dim">
                      Live koers ophalen…
                    </Text>
                  </Flex>
                ) : liveQuote ? (
                  <>
                    <DetailRow
                      label="Live koers"
                      value={`${formatSmartEur(liveQuote.price_eur)} / st.`}
                      highlight
                    />
                    {liveQuote.market_label ? (
                      <>
                        <Divider borderColor="azure.100" />
                        <DetailRow label="Beurs" value={liveQuote.market_label} />
                      </>
                    ) : null}
                    <Divider borderColor="azure.100" />
                    <DetailRow
                      label="Bron"
                      value={livePriceSourceLabel(liveQuote.source)}
                    />
                    <Divider borderColor="azure.100" />
                    <DetailRow
                      label="Bijgewerkt"
                      value={formatLiveFetchedAt(liveQuote.fetched_at)}
                    />
                    {priceDeltaLabel && tx.price_eur ? (
                      <>
                        <Divider borderColor="azure.100" />
                        <DetailRow
                          label="Verschil"
                          value={priceDeltaLabel}
                          highlight={priceDelta !== null && priceDelta >= 0}
                        />
                      </>
                    ) : null}
                  </>
                ) : (
                  <Text py={4} fontSize="sm" color="ink.dim" textAlign="center">
                    Live koers niet beschikbaar voor dit instrument.
                  </Text>
                )}
              </Box>
              <Text fontSize="xs" color="ink.faint" mt={2} lineHeight={1.6}>
                {liveQuote?.market_label
                  ? `Koers in euro van ${liveQuote.market_label}. Andere beursnoteringen van hetzelfde fonds (bijv. .IR, .L of USD) kunnen afwijken — wij tonen de EUR-notering passend bij uw ISIN.`
                  : "Koers in euro via Yahoo Finance of uw broker-feed."}
                {tx.transaction_type === "dividend"
                  ? " Dit is de huidige ETF-koers, niet het dividendbedrag."
                  : null}
              </Text>
            </Box>
          )}

          <Box mb={6}>
            <SectionTitle>{exportSectionTitle(tx.transaction_type)}</SectionTitle>
            <Box bg="paper" border="1px solid" borderColor="line.soft" borderRadius="md" px={4}>
              <DetailRow label={quantityLabel(tx.transaction_type)} value={formatQuantity(tx.quantity)} />
              <Divider borderColor="line.soft" />
              <DetailRow
                label={unitAmountLabel(tx.transaction_type)}
                value={tx.price_eur ? `${formatSmartEur(tx.price_eur)} / st.` : "—"}
              />
              <Divider borderColor="line.soft" />
              <DetailRow label="Kosten" value={fee > 0 ? formatEur(fee) : "—"} />
              <Divider borderColor="line.soft" />
              <DetailRow
                label={tx.transaction_type === "dividend" ? "Totaal ontvangen" : "Totaal"}
                value={tx.total_eur ? formatEur(tx.total_eur) : "—"}
              />
            </Box>
            <Text fontSize="xs" color="ink.faint" mt={2} lineHeight={1.6}>
              {tx.transaction_type === "dividend"
                ? "Bij dividend is het prijsveld in de export het dividend per stuk, geen beurskoers."
                : null}
              {tx.transaction_type === "dividend" ? " " : null}
              {tx.import_label
                ? `Vastgelegd uit ${platformLabel(tx.source_platform) || "broker"}-export (${tx.import_label}).`
                : "Handmatig ingevoerd of via platform-sync."}
            </Text>
          </Box>

          <Box mb={6}>
            <SectionTitle>Herkomst</SectionTitle>
            <Box bg="paper" border="1px solid" borderColor="line.soft" borderRadius="md" px={4}>
              <DetailRow
                label="Transactietype"
                value={transactionTypeLabel(tx.transaction_type)}
              />
              <Divider borderColor="line.soft" />
              <DetailRow label="Platform" value={platformLabel(tx.source_platform) || "Handmatig"} />
              <Divider borderColor="line.soft" />
              <DetailRow
                label="Import"
                value={
                  tx.import_label ? (
                    importHref ? (
                      <Link
                        as={RouterLink}
                        to={importHref}
                        color="azure.600"
                        fontWeight={600}
                        _hover={{ textDecoration: "underline" }}
                        onClick={onClose}
                      >
                        {tx.import_label}
                      </Link>
                    ) : (
                      tx.import_label
                    )
                  ) : (
                    "Handmatig of losse regel"
                  )
                }
              />
            </Box>
          </Box>

          <Box mb={2}>
            <SectionTitle>Administratie</SectionTitle>
            <Box bg="paper" border="1px solid" borderColor="line.soft" borderRadius="md" px={4}>
              <DetailRow label="Transactiedatum" value={formatDateTimeNl(tx.occurred_at)} />
              <Divider borderColor="line.soft" />
              <DetailRow label="Opgeslagen op" value={formatDateNl(tx.created_at)} />
              {tx.external_id ? (
                <>
                  <Divider borderColor="line.soft" />
                  <DetailRow label="Extern ID" value={tx.external_id} mono />
                </>
              ) : null}
              {tx.notes?.trim() ? (
                <>
                  <Divider borderColor="line.soft" />
                  <Grid templateColumns="1fr" gap={1} py={2.5}>
                    <Text fontSize="sm" color="ink.dim">
                      Notities
                    </Text>
                    <Text fontSize="sm" color="ink.primary" whiteSpace="pre-wrap">
                      {tx.notes.trim()}
                    </Text>
                  </Grid>
                </>
              ) : null}
            </Box>
          </Box>
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  );
}
