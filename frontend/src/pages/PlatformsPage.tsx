import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Flex,
  SimpleGrid,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import {
  deleteConnection,
  purgeConnectionData,
  type CsvImportResult,
  listConnections,
  pollSyncJob,
  triggerSync,
  type PlatformConnection,
} from "../api/integrations";
import CsvImportWizard, {
  formatPreviewMessage,
} from "../components/platforms/CsvImportWizard";
import { getDashboardSummary } from "../api/portfolio";
import AuthAlert from "../components/auth/AuthAlert";
import SectionHeader from "../components/common/SectionHeader";
import StatStrip from "../components/common/StatStrip";
import ConnectionRowCard from "../components/platforms/ConnectionRowCard";
import PlatformBrowseCard from "../components/platforms/PlatformBrowseCard";
import MotionSection from "../components/layout/MotionSection";
import PageHeader from "../components/layout/PageHeader";
import PageShell from "../components/layout/PageShell";
import {
  METHOD_META,
  PLATFORM_CATALOG,
  type IntegrationMethod,
} from "../data/platformCatalog";
import { useUser } from "../contexts/UserContext";
import { formatEur } from "../utils/formatMoney";
import { LIVE_CSV_PLATFORMS } from "../utils/platformLabels";
import { getApiErrorMessage } from "../utils/apiError";

const BROWSE_PLATFORMS = PLATFORM_CATALOG.filter((p) =>
  ["coinbase", "ibkr", "trading212", "abn"].includes(p.id),
);

function mapConnectionMethod(method: string): IntegrationMethod {
  if (method === "api") return "api";
  if (method === "csv") return "csv";
  return "manual";
}

export default function PlatformsPage() {
  const navigate = useNavigate();
  const { user } = useUser();
  const location = useLocation();
  const [connections, setConnections] = useState<PlatformConnection[]>([]);
  const [platformStats, setPlatformStats] = useState<
    Record<number, { value: string; holdings: number }>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState(
    (location.state as { message?: string } | null)?.message ?? "",
  );
  const [syncingId, setSyncingId] = useState<number | null>(null);
  const [csvWizardOpen, setCsvWizardOpen] = useState(false);
  const [csvWizardFile, setCsvWizardFile] = useState<File | null>(null);
  const [csvWizardPlatform, setCsvWizardPlatform] = useState<string | undefined>(undefined);
  const csvInputRef = useRef<HTMLInputElement>(null);
  const csvSectionRef = useRef<HTMLDivElement>(null);

  const loadConnections = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [data, summary] = await Promise.all([
        listConnections(),
        getDashboardSummary().catch(() => null),
      ]);
      setConnections(data);
      if (summary?.platforms) {
        const stats: Record<number, { value: string; holdings: number }> = {};
        for (const p of summary.platforms) {
          stats[p.id] = {
            value: formatEur(summary.total_value_eur),
            holdings: summary.positions_count,
          };
        }
        setPlatformStats(stats);
      }
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Platformen laden mislukt."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadConnections();
  }, [loadConnections]);

  useEffect(() => {
    const state = location.state as {
      focusDegiroCsv?: boolean;
      focusCsvPlatform?: string;
    } | null;
    const platform = state?.focusCsvPlatform ?? (state?.focusDegiroCsv ? "degiro" : null);
    if (!platform) {
      return;
    }
    navigate(location.pathname, { replace: true, state: {} });
    setCsvWizardPlatform(platform);
    const timer = window.setTimeout(() => {
      csvSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 300);
    return () => window.clearTimeout(timer);
  }, [location.pathname, location.state, navigate]);

  const grouped = useMemo(() => {
    const groups: Record<IntegrationMethod, PlatformConnection[]> = {
      api: [],
      csv: [],
      year: [],
      manual: [],
    };
    for (const c of connections) {
      groups[mapConnectionMethod(c.connection_method)].push(c);
    }
    return groups;
  }, [connections]);

  const statCounts = useMemo(
    () => ({
      api: grouped.api.length,
      csv: grouped.csv.length,
      year: grouped.year.length,
      manual: grouped.manual.length,
    }),
    [grouped],
  );

  async function handleSync(connection: PlatformConnection) {
    setError("");
    setMessage("");
    setSyncingId(connection.id);
    try {
      const job = await triggerSync(connection.id);
      const result = await pollSyncJob(job.id);
      if (result.status === "error") {
        setError(result.error_message || "Synchronisatie mislukt.");
      } else {
        setMessage(
          `Synchronisatie voltooid: ${result.positions_synced} posities, ${result.transactions_synced} transacties.`,
        );
      }
      await loadConnections();
    } catch (syncError) {
      setError(getApiErrorMessage(syncError, "Synchronisatie mislukt."));
    } finally {
      setSyncingId(null);
    }
  }

  function openCsvWizard(file: File) {
    setCsvWizardFile(file);
    setCsvWizardOpen(true);
  }

  function handleCsvWizardComplete(result: CsvImportResult) {
    setMessage(formatPreviewMessage(result));
    void loadConnections();
    if (csvInputRef.current) csvInputRef.current.value = "";
  }

  async function handleDisconnect(connection: PlatformConnection) {
    if (
      !window.confirm(
        `Weet u zeker dat u ${connection.display_name} wilt loskoppelen? Uw transacties blijven bewaard.`,
      )
    ) {
      return;
    }
    setError("");
    try {
      await deleteConnection(connection.id);
      setMessage(`${connection.display_name} is losgekoppeld. Uw transacties blijven bewaard.`);
      await loadConnections();
    } catch (deleteError) {
      setError(getApiErrorMessage(deleteError, "Loskoppelen mislukt."));
    }
  }

  async function handlePurgeData(connection: PlatformConnection) {
    if (
      !window.confirm(
        `Alle importdata van ${connection.display_name} wordt permanent verwijderd, inclusief transacties en posities. Doorgaan?`,
      )
    ) {
      return;
    }
    setError("");
    try {
      const result = await purgeConnectionData(connection.id);
      setMessage(
        `${result.transactions_deleted} transactie(s) verwijderd (${result.import_batches_deleted} import(s)).`,
      );
      await loadConnections();
    } catch (purgeError) {
      setError(getApiErrorMessage(purgeError, "Data wissen mislukt."));
    }
  }

  function secondaryForConnection(c: PlatformConnection): string | undefined {
    const stats = platformStats[c.id];
    if (stats) {
      return `${stats.value} · ${stats.holdings} posities`;
    }
    return undefined;
  }

  function renderGroup(method: IntegrationMethod) {
    const meta = METHOD_META[method];
    const items = grouped[method];
    const addHref =
      method === "api"
        ? "/platforms/add?method=api"
        : method === "csv"
          ? "/platforms/add?method=csv"
          : method === "year"
            ? "/platforms/add?method=year"
            : "/portfolio/manual/asset";

    return (
      <MotionSection key={method}>
        <SectionHeader
          title={
            <>
              {meta.title.split(" · ")[0]}{" "}
              <Text as="em">· {meta.title.split(" · ").slice(1).join(" · ") || meta.subtitle}</Text>
            </>
          }
          kicker={meta.subtitle}
        />
        {items.length === 0 ? (
          <Text fontSize="sm" color="ink.dim" fontStyle="italic" mb={3}>
            Nog geen {meta.label.toLowerCase()} gekoppeld.
          </Text>
        ) : (
          <VStack align="stretch" spacing={3} mb={3}>
            {items.map((connection) => (
              <ConnectionRowCard
                key={connection.id}
                connection={connection}
                secondaryLine={secondaryForConnection(connection)}
                syncing={syncingId === connection.id}
                onSync={
                  connection.connection_method === "api"
                    ? () => void handleSync(connection)
                    : undefined
                }
                onManage={
                  connection.connection_method === "csv"
                    ? () => {
                        setCsvWizardPlatform(connection.platform);
                        csvInputRef.current?.click();
                      }
                    : () => navigate("/platforms/add")
                }
                onDisconnect={() => void handleDisconnect(connection)}
                onPurgeData={() => void handlePurgeData(connection)}
                onImportHistoryChanged={() => void loadConnections()}
                primaryActionLabel={
                  connection.connection_method === "csv" ? "↺ Recentere upload" : undefined
                }
              />
            ))}
          </VStack>
        )}
        <Button
          as={RouterLink}
          to={addHref}
          variant="ghostNav"
          size="sm"
          fontWeight={500}
          color="azure.500"
          _hover={{ bg: "azure.50" }}
        >
          {meta.addLabel}
        </Button>
      </MotionSection>
    );
  }

  return (
    <PageShell>
      <MotionSection>
        <PageHeader
          kicker="Platform-integraties"
          title={
            <>
              Gekoppelde <Text as="em">platformen</Text>
            </>
          }
          subtitle="Beheer de verbindingen met uw brokers, exchanges en banken. Bekijk per platform welk type koppeling actief is en wanneer de laatste data binnenkwam."
          actions={
            <Flex gap={2} flexWrap="wrap">
              <Button as={RouterLink} to="/platforms/vergelijker" variant="fiscalOutline" size="sm">
                Platformen vergelijken
              </Button>
              <Button as={RouterLink} to="/platforms/add" variant="fiscal" size="sm">
                + Platform toevoegen
              </Button>
            </Flex>
          }
        />
      </MotionSection>

      {user && !user.email_verified && (
        <MotionSection>
          <AuthAlert tone="info">
            Bevestig eerst uw e-mailadres voordat u een platform kunt koppelen.
          </AuthAlert>
        </MotionSection>
      )}
      {error && (
        <MotionSection>
          <AuthAlert tone="error">{error}</AuthAlert>
        </MotionSection>
      )}
      {message && (
        <MotionSection>
          <AuthAlert tone="success">{message}</AuthAlert>
        </MotionSection>
      )}

      <input
        ref={csvInputRef}
        type="file"
        accept=".csv,text/csv"
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) openCsvWizard(f);
        }}
      />

      {!loading && (
        <MotionSection>
          <StatStrip
            items={[
              {
                label: "API-koppelingen",
                value: statCounts.api,
                sub: "realtime sync",
                tone: statCounts.api > 0 ? "moss" : "default",
              },
              {
                label: "CSV-uploads",
                value: statCounts.csv,
                sub: "periodieke upload",
                tone: statCounts.csv > 0 ? "ochre" : "default",
              },
              {
                label: "Jaaroverzicht",
                value: statCounts.year,
                sub: "jaarlijks PDF",
              },
              {
                label: "Handmatig",
                value: statCounts.manual,
                sub: "zelf bijgehouden",
              },
            ]}
          />
        </MotionSection>
      )}

      {loading ? (
        <Text color="ink.dim" fontStyle="italic">
          Platformen laden…
        </Text>
      ) : (
        <>
          {(["api", "csv", "year", "manual"] as IntegrationMethod[]).map(renderGroup)}

          <MotionSection>
            <SectionHeader
              title={
                <>
                  Platform <Text as="em">zoeken</Text>
                </>
              }
              kicker="blader door 30+ ondersteunde platformen"
            />
            <SimpleGrid columns={{ base: 1, sm: 2, lg: 4 }} spacing={4}>
              {BROWSE_PLATFORMS.map((p) => (
                <PlatformBrowseCard key={p.id} platform={p} />
              ))}
            </SimpleGrid>
            <Button
              as={RouterLink}
              to="/platforms/add"
              variant="fiscalOutline"
              size="sm"
              mt={4}
            >
              Toon alle platformen →
            </Button>
          </MotionSection>

          <MotionSection>
            <Box
              ref={csvSectionRef}
              p={5}
              border="1px dashed"
              borderColor="line.DEFAULT"
              borderRadius="base"
              bg="backgroundHover"
            >
              <Text fontWeight={600} mb={2}>
                CSV-import
              </Text>
              <Text fontSize="sm" color="ink.dim" mb={4} lineHeight={1.7}>
                Upload een transactie-export. Ondersteund: DEGIRO, Trading 212, Trade Republic,
                Bybit en OKX. Auto-detectie op kolomkoppen; preview vóór import.
              </Text>
              <Flex gap={2} flexWrap="wrap">
                {LIVE_CSV_PLATFORMS.map((p) => (
                  <Button
                    key={p.id}
                    variant={csvWizardPlatform === p.id ? "fiscal" : "fiscalOutline"}
                    size="sm"
                    isDisabled={!user?.email_verified}
                    onClick={() => {
                      setCsvWizardPlatform(p.id);
                      csvInputRef.current?.click();
                    }}
                  >
                    {p.name} CSV
                  </Button>
                ))}
              </Flex>
            </Box>
          </MotionSection>
        </>
      )}
      <CsvImportWizard
        isOpen={csvWizardOpen}
        file={csvWizardFile}
        platform={csvWizardPlatform}
        onClose={() => {
          setCsvWizardOpen(false);
          setCsvWizardFile(null);
        }}
        onComplete={handleCsvWizardComplete}
      />
    </PageShell>
  );
}
