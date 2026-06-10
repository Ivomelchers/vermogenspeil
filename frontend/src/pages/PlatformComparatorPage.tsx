import { useMemo, useState, type ReactNode } from "react";
import {
  Box,
  Button,
  Flex,
  Grid,
  Input,
  Text,
} from "@chakra-ui/react";

import {
  CATEGORY_LABELS,
  PLATFORM_CATALOG,
  type CatalogPlatform,
  type IntegrationMethod,
  type PlatformCategory,
} from "../data/platformCatalog";
import FiscalDisclaimer from "../components/common/FiscalDisclaimer";
import { fiscalScrollbarSx } from "../styles/scrollbar";
import ComparatorPlatformCard from "../components/platforms/ComparatorPlatformCard";
import PlatformComparatorQuiz from "../components/platforms/PlatformComparatorQuiz";
import PlatformDetailModal from "../components/platforms/PlatformDetailModal";
import MotionSection from "../components/layout/MotionSection";
import PageHeader from "../components/layout/PageHeader";
import PageShell from "../components/layout/PageShell";

type CatFilter = "all" | PlatformCategory;
type IntFilter = "all" | IntegrationMethod;

const CATEGORY_ORDER: PlatformCategory[] = ["crypto", "broker", "metal", "bank"];

export default function PlatformComparatorPage() {
  const [search, setSearch] = useState("");
  const [catFilter, setCatFilter] = useState<CatFilter>("all");
  const [intFilter, setIntFilter] = useState<IntFilter>("all");
  const [detailPlatform, setDetailPlatform] = useState<CatalogPlatform | null>(null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return PLATFORM_CATALOG.filter((p) => {
      if (catFilter !== "all" && p.category !== catFilter) return false;
      if (intFilter !== "all" && !p.methods.includes(intFilter)) return false;
      if (!q) return true;
      return (
        p.name.toLowerCase().includes(q) ||
        p.country.toLowerCase().includes(q) ||
        p.typeLabel.toLowerCase().includes(q) ||
        p.searchTerms?.includes(q) ||
        p.features.some((f) => f.toLowerCase().includes(q))
      );
    });
  }, [search, catFilter, intFilter]);

  const grouped = useMemo(() => {
    const groups: Partial<Record<PlatformCategory, CatalogPlatform[]>> = {};
    for (const p of filtered) {
      if (!groups[p.category]) groups[p.category] = [];
      groups[p.category]!.push(p);
    }
    return groups;
  }, [filtered]);

  return (
    <PageShell wide>
      <MotionSection>
        <PageHeader
          kicker="Platform-vergelijker"
          title={
            <>
              Platformen <Text as="em">vergelijken</Text>
            </>
          }
          subtitle="Kies op basis van kosten, aanbod, regulering en gebruiksgemak — of gebruik de vragenlijst. Geen advies, enkel informatie."
        />
      </MotionSection>

      <MotionSection>
        <FiscalDisclaimer>
          <strong>Let op:</strong> gebaseerd op openbare gegevens. Verbox biedt geen
          beleggingsadvies. Bitvavo, Bybit, OKX (API), DEGIRO, Trading 212, Trade Republic (CSV) zijn live;
          platformen staan in de catalogus.
        </FiscalDisclaimer>
      </MotionSection>

      <Grid templateColumns={{ base: "1fr", xl: "1fr 320px" }} gap={8} alignItems="start">
        <Box>
          <MotionSection>
            <Input
              variant="fiscal"
              placeholder="Zoek platform… (bijv. DEGIRO, Bitvavo)"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              mb={4}
            />
            <Flex gap={2} flexWrap="wrap" mb={3}>
              <FilterPill active={catFilter === "all"} onClick={() => setCatFilter("all")}>
                Alle
              </FilterPill>
              {(Object.keys(CATEGORY_LABELS) as PlatformCategory[]).map((cat) => (
                <FilterPill
                  key={cat}
                  active={catFilter === cat}
                  onClick={() => setCatFilter(cat)}
                >
                  {CATEGORY_LABELS[cat]}
                </FilterPill>
              ))}
            </Flex>
            <Flex gap={2} flexWrap="wrap" mb={6}>
              <FilterPill active={intFilter === "all"} onClick={() => setIntFilter("all")}>
                Alle koppelingen
              </FilterPill>
              <FilterPill active={intFilter === "api"} onClick={() => setIntFilter("api")}>
                API
              </FilterPill>
              <FilterPill active={intFilter === "csv"} onClick={() => setIntFilter("csv")}>
                CSV
              </FilterPill>
              <FilterPill active={intFilter === "year"} onClick={() => setIntFilter("year")}>
                Jaaropgave
              </FilterPill>
              <FilterPill active={intFilter === "manual"} onClick={() => setIntFilter("manual")}>
                Handmatig
              </FilterPill>
            </Flex>
            <Text fontSize="sm" color="ink.dim" mb={6}>
              {filtered.length} platform{filtered.length === 1 ? "" : "en"} gevonden
            </Text>
          </MotionSection>

          {filtered.length === 0 ? (
            <Text color="ink.dim" fontStyle="italic">
              Geen platformen voor deze filters. Wis de zoekterm of kies &quot;Alle&quot;.
            </Text>
          ) : (
            CATEGORY_ORDER.filter((cat) => grouped[cat]?.length).map((cat) => (
              <MotionSection key={cat}>
                <Text fontFamily="heading" fontSize="xl" mb={1}>
                  {CATEGORY_LABELS[cat]}
                </Text>
                <Text fontSize="sm" color="ink.dim" mb={4}>
                  {grouped[cat]!.length} platformen
                </Text>
                <Box
                  overflowX="auto"
                  pb={2}
                  sx={fiscalScrollbarSx("horizontal")}
                >
                  <Flex gap={4} py={1}>
                    {grouped[cat]!.map((platform) => (
                      <ComparatorPlatformCard
                        key={platform.id}
                        platform={platform}
                        onMoreInfo={() => setDetailPlatform(platform)}
                      />
                    ))}
                  </Flex>
                </Box>
              </MotionSection>
            ))
          )}
        </Box>

        <Box display={{ base: "none", xl: "block" }}>
          <PlatformComparatorQuiz />
        </Box>
      </Grid>

      <Box display={{ base: "block", xl: "none" }} mt={8}>
        <PlatformComparatorQuiz />
      </Box>

      <PlatformDetailModal
        platform={detailPlatform}
        isOpen={detailPlatform != null}
        onClose={() => setDetailPlatform(null)}
      />
    </PageShell>
  );
}

function FilterPill({
  children,
  active,
  onClick,
}: {
  children: ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <Button
      size="sm"
      variant={active ? "fiscal" : "fiscalOutline"}
      onClick={onClick}
      fontSize="xs"
      px={3}
    >
      {children}
    </Button>
  );
}
