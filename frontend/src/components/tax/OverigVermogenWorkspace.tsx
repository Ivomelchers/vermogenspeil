import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  Grid,
  Input,
  Select,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  VStack,
} from "@chakra-ui/react";

import {
  createBox3BankBalance,
  createBox3Debt,
  createBox3RealEstate,
  deleteBox3BankBalance,
  deleteBox3Debt,
  deleteBox3RealEstate,
  listBox3BankBalances,
  listBox3Debts,
  listBox3RealEstate,
  type Box3BankBalance,
  type Box3Debt,
  type Box3RealEstate,
} from "../../api/tax";
import AuthAlert from "../auth/AuthAlert";
import FiscalCard from "../common/FiscalCard";
import StatStrip from "../common/StatStrip";
import { useUser } from "../../contexts/UserContext";
import { formatEur } from "../../utils/formatMoney";
import { getApiErrorMessage } from "../../utils/apiError";

const BANK_TYPES = [
  { value: "savings", label: "Spaarrekening" },
  { value: "checking", label: "Betaalrekening" },
  { value: "deposit", label: "Depositorekening" },
  { value: "other", label: "Overig banktegoed" },
];

const DEBT_TYPES = [
  { value: "consumer", label: "Consumptief" },
  { value: "investment", label: "Beleggingsfinanciering" },
  { value: "mortgage_second_home", label: "Hypotheek 2e woning" },
  { value: "negative_balance", label: "Negatief banksaldo" },
  { value: "other", label: "Overig" },
];

const PROPERTY_TYPES = [
  { value: "second_home_nl", label: "2e woning NL" },
  { value: "second_home_abroad", label: "2e woning buitenland" },
  { value: "rental_nl", label: "Verhuurd NL" },
  { value: "rental_abroad", label: "Verhuurd buitenland" },
  { value: "other", label: "Overig onroerend" },
];

const SCHULD_DREMPEL_BASE = 3800;

function parseAmount(v: string): number {
  const n = parseFloat(v.replace(",", "."));
  return Number.isFinite(n) ? n : 0;
}

interface OverigVermogenWorkspaceProps {
  taxYear: number;
}

export default function OverigVermogenWorkspace({ taxYear }: OverigVermogenWorkspaceProps) {
  const { user } = useUser();
  const [banks, setBanks] = useState<Box3BankBalance[]>([]);
  const [debts, setDebts] = useState<Box3Debt[]>([]);
  const [properties, setProperties] = useState<Box3RealEstate[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [tabIndex, setTabIndex] = useState(0);

  const [bankError, setBankError] = useState("");
  const [debtError, setDebtError] = useState("");
  const [propertyError, setPropertyError] = useState("");
  const [busy, setBusy] = useState(false);

  const [bankLabel, setBankLabel] = useState("");
  const [bankType, setBankType] = useState("savings");
  const [bankBalance, setBankBalance] = useState("");

  const [debtLabel, setDebtLabel] = useState("");
  const [debtType, setDebtType] = useState("other");
  const [debtOutstanding, setDebtOutstanding] = useState("");
  const [debtInterest, setDebtInterest] = useState("0");
  const [debtLinkedProperty, setDebtLinkedProperty] = useState("");

  const [propLabel, setPropLabel] = useState("");
  const [propType, setPropType] = useState("second_home_nl");
  const [propValue, setPropValue] = useState("");
  const [propRentYtd, setPropRentYtd] = useState("0");
  const [propAnnualRent, setPropAnnualRent] = useState("0");
  const [propVacancy, setPropVacancy] = useState("0");
  const [propWoz, setPropWoz] = useState("");
  const [propEigenDays, setPropEigenDays] = useState("365");
  const [propVerhuurDays, setPropVerhuurDays] = useState("0");
  const [propVerbouwDays, setPropVerbouwDays] = useState("0");
  const [propBijtelling, setPropBijtelling] = useState("woz_vast");
  const [propEconomicRent, setPropEconomicRent] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const [b, d, p] = await Promise.all([
        listBox3BankBalances(taxYear),
        listBox3Debts(taxYear),
        listBox3RealEstate(taxYear),
      ]);
      setBanks(b);
      setDebts(d);
      setProperties(p);
    } catch (err) {
      setLoadError(getApiErrorMessage(err, "Overig vermogen laden mislukt."));
    } finally {
      setLoading(false);
    }
  }, [taxYear]);

  useEffect(() => {
    void load();
  }, [load]);

  const totals = useMemo(() => {
    const bankTotal = banks.reduce((s, b) => s + parseAmount(b.balance_eur), 0);
    const debtTotal = debts.reduce((s, d) => s + parseAmount(d.outstanding_eur), 0);
    const propertyTotal = properties.reduce((s, p) => s + parseAmount(p.value_eur), 0);
    const threshold = SCHULD_DREMPEL_BASE * (user?.has_fiscal_partner ? 2 : 1);
    const debtDeductible = Math.max(0, debtTotal - threshold);
    return { bankTotal, debtTotal, propertyTotal, threshold, debtDeductible };
  }, [banks, debts, properties, user?.has_fiscal_partner]);

  function notifySuccess(msg: string) {
    setSuccessMessage(msg);
    window.setTimeout(() => setSuccessMessage(""), 4000);
  }

  async function handleAddBank() {
    if (!bankLabel.trim() || !bankBalance.trim()) {
      setBankError("Vul minimaal omschrijving en saldo in.");
      return;
    }
    setBusy(true);
    setBankError("");
    try {
      await createBox3BankBalance({
        tax_year: taxYear,
        label: bankLabel.trim(),
        account_type: bankType,
        balance_eur: bankBalance.replace(",", "."),
        institution: "",
        notes: "",
      });
      setBankLabel("");
      setBankBalance("");
      await load();
      notifySuccess("Banktegoed opgeslagen.");
    } catch (e) {
      setBankError(getApiErrorMessage(e, "Opslaan mislukt."));
    } finally {
      setBusy(false);
    }
  }

  async function handleAddDebt() {
    if (!debtLabel.trim() || !debtOutstanding.trim()) {
      setDebtError("Vul minimaal omschrijving en schuldsaldo in.");
      return;
    }
    setBusy(true);
    setDebtError("");
    try {
      await createBox3Debt({
        tax_year: taxYear,
        label: debtLabel.trim(),
        debt_type: debtType,
        outstanding_eur: debtOutstanding.replace(",", "."),
        interest_paid_ytd_eur: debtInterest.replace(",", ".") || "0",
        creditor: "",
        linked_real_estate: debtLinkedProperty ? Number(debtLinkedProperty) : null,
        notes: "",
      });
      setDebtLabel("");
      setDebtOutstanding("");
      setDebtInterest("0");
      setDebtLinkedProperty("");
      await load();
      notifySuccess("Schuld opgeslagen.");
    } catch (e) {
      setDebtError(getApiErrorMessage(e, "Opslaan mislukt."));
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteProperty(id: number) {
    setBusy(true);
    setPropertyError("");
    try {
      await deleteBox3RealEstate(id);
      await load();
      notifySuccess("Vastgoed verwijderd.");
    } catch (e) {
      setPropertyError(getApiErrorMessage(e, "Verwijderen mislukt."));
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteDebt(id: number) {
    setBusy(true);
    setDebtError("");
    try {
      await deleteBox3Debt(id);
      await load();
      notifySuccess("Schuld verwijderd.");
    } catch (e) {
      setDebtError(getApiErrorMessage(e, "Verwijderen mislukt."));
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteBank(id: number) {
    setBusy(true);
    setBankError("");
    try {
      await deleteBox3BankBalance(id);
      await load();
      notifySuccess("Banktegoed verwijderd.");
    } catch (e) {
      setBankError(getApiErrorMessage(e, "Verwijderen mislukt."));
    } finally {
      setBusy(false);
    }
  }

  async function handleAddProperty() {
    if (!propLabel.trim() || !propValue.trim()) {
      setPropertyError("Vul minimaal omschrijving en waarde in.");
      return;
    }
    const isAbroad = propType.includes("abroad");
    setBusy(true);
    setPropertyError("");
    try {
      await createBox3RealEstate({
        tax_year: taxYear,
        label: propLabel.trim(),
        property_type: propType,
        value_eur: propValue.replace(",", "."),
        is_abroad: isAbroad,
        annual_rent_eur: propAnnualRent.replace(",", ".") || "0",
        vacancy_ratio: propVacancy.replace(",", ".") || "0",
        rental_income_ytd_eur: propRentYtd.replace(",", ".") || "0",
        eigen_gebruik_days: Number(propEigenDays) || 0,
        verhuur_days: Number(propVerhuurDays) || 0,
        verbouw_days: Number(propVerbouwDays) || 0,
        bijtelling_method: propBijtelling,
        economic_rent_yearly_eur:
          propBijtelling === "huurwaarde" ? propEconomicRent.replace(",", ".") || "0" : "0",
        woz_previous_year_eur: propWoz.replace(",", ".") || propValue.replace(",", "."),
        bijtelling_rate: "0.0275",
        notes: "",
      });
      setPropLabel("");
      setPropValue("");
      setPropRentYtd("0");
      setPropWoz("");
      await load();
      notifySuccess("Vastgoed opgeslagen.");
    } catch (e) {
      setPropertyError(getApiErrorMessage(e, "Opslaan mislukt."));
    } finally {
      setBusy(false);
    }
  }

  const inputSx = { variant: "fiscal" as const, size: "sm" as const };

  if (loading) {
    return (
      <Text color="ink.dim" fontStyle="italic">
        Overig vermogen laden…
      </Text>
    );
  }

  return (
    <VStack align="stretch" spacing={6}>
      {loadError && <AuthAlert tone="error">{loadError}</AuthAlert>}
      {successMessage && <AuthAlert tone="success">{successMessage}</AuthAlert>}

      <StatStrip
        items={[
          {
            label: "Banktegoeden (B)",
            value: formatEur(String(totals.bankTotal)),
            sub: `${banks.length} rekening${banks.length === 1 ? "" : "en"}`,
            tone: banks.length > 0 ? "moss" : "default",
          },
          {
            label: "Schulden (S)",
            value: formatEur(String(totals.debtTotal)),
            sub: `drempel ${formatEur(String(totals.threshold))}`,
            tone: "ochre",
          },
          {
            label: "Aftrekbaar schuld",
            value: formatEur(String(totals.debtDeductible)),
            sub: "boven schuldendrempel",
          },
          {
            label: "Vastgoed (O)",
            value: formatEur(String(totals.propertyTotal)),
            sub: `${properties.length} object${properties.length === 1 ? "" : "en"}`,
          },
        ]}
      />

      <Tabs
        index={tabIndex}
        onChange={setTabIndex}
        variant="unstyled"
        sx={{
          ".chakra-tabs__tablist": {
            borderBottom: "1px solid",
            borderColor: "line.soft",
            gap: 0,
          },
          ".chakra-tabs__tab": {
            fontFamily: "heading",
            fontSize: "sm",
            color: "ink.dim",
            pb: 3,
            px: 4,
            borderBottom: "2px solid transparent",
            _selected: { color: "ink.primary", borderColor: "azure.500" },
          },
        }}
      >
        <TabList>
          <Tab>Vastgoed ({properties.length})</Tab>
          <Tab>Schulden ({debts.length})</Tab>
          <Tab>Banktegoeden ({banks.length})</Tab>
        </TabList>

        <TabPanels pt={6}>
          <TabPanel px={0}>
            {properties.map((p) => (
              <FiscalCard key={p.id} elevated p={4} mb={3}>
                <Flex justify="space-between" align="flex-start" gap={4} flexWrap="wrap">
                  <Box>
                    <Text fontWeight={600} fontFamily="heading">
                      {p.label}
                    </Text>
                    <Text fontSize="sm" color="ink.dim">
                      Waarde {formatEur(p.value_eur)}
                      {p.bijtelling_eur && ` · bijtelling ${formatEur(p.bijtelling_eur)}`}
                      {p.rental_income_ytd_eur !== "0" &&
                        ` · huur YTD ${formatEur(p.rental_income_ytd_eur)}`}
                    </Text>
                  </Box>
                  <Button
                    size="sm"
                    variant="fiscalOutline"
                    color="rust.500"
                    isDisabled={busy}
                    onClick={() => void handleDeleteProperty(p.id)}
                  >
                    Verwijderen
                  </Button>
                </Flex>
              </FiscalCard>
            ))}
            <FiscalCard elevated p={5}>
              <Text fontWeight={600} mb={4}>
                Vastgoed toevoegen
              </Text>
              <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={3}>
                <FormControl isRequired>
                  <FormLabel fontSize="sm">Omschrijving</FormLabel>
                  <Input {...inputSx} value={propLabel} onChange={(e) => setPropLabel(e.target.value)} placeholder="Vakantiehuis Zeeland" />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Type</FormLabel>
                  <Select size="sm" value={propType} onChange={(e) => setPropType(e.target.value)}>
                    {PROPERTY_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </Select>
                </FormControl>
                <FormControl isRequired>
                  <FormLabel fontSize="sm">Waarde peildatum (€)</FormLabel>
                  <Input {...inputSx} inputMode="decimal" value={propValue} onChange={(e) => setPropValue(e.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">WOZ vorig jaar (€)</FormLabel>
                  <Input {...inputSx} inputMode="decimal" value={propWoz} onChange={(e) => setPropWoz(e.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Eigen gebruik (dagen)</FormLabel>
                  <Input {...inputSx} inputMode="numeric" value={propEigenDays} onChange={(e) => setPropEigenDays(e.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Verhuur (dagen)</FormLabel>
                  <Input {...inputSx} inputMode="numeric" value={propVerhuurDays} onChange={(e) => setPropVerhuurDays(e.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Huurinkomsten YTD (€)</FormLabel>
                  <Input {...inputSx} inputMode="decimal" value={propRentYtd} onChange={(e) => setPropRentYtd(e.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Jaarhuur contract (€)</FormLabel>
                  <Input {...inputSx} inputMode="decimal" value={propAnnualRent} onChange={(e) => setPropAnnualRent(e.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Leegstand (%)</FormLabel>
                  <Input {...inputSx} inputMode="decimal" value={propVacancy} onChange={(e) => setPropVacancy(e.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Verbouw (dagen)</FormLabel>
                  <Input {...inputSx} inputMode="numeric" value={propVerbouwDays} onChange={(e) => setPropVerbouwDays(e.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Bijtelling</FormLabel>
                  <Select size="sm" value={propBijtelling} onChange={(e) => setPropBijtelling(e.target.value)}>
                    <option value="woz_vast">Vast % WOZ</option>
                    <option value="huurwaarde">Economische huurwaarde</option>
                  </Select>
                </FormControl>
                {propBijtelling === "huurwaarde" && (
                  <FormControl>
                    <FormLabel fontSize="sm">Economische huur per jaar (€)</FormLabel>
                    <Input {...inputSx} inputMode="decimal" value={propEconomicRent} onChange={(e) => setPropEconomicRent(e.target.value)} />
                  </FormControl>
                )}
              </Grid>
              <Button variant="fiscal" size="sm" mt={4} isLoading={busy} onClick={() => void handleAddProperty()}>
                + Vastgoed toevoegen
              </Button>
              {propertyError && <Text fontSize="sm" color="rust.500" mt={2}>{propertyError}</Text>}
            </FiscalCard>
          </TabPanel>

          <TabPanel px={0}>
            <SimpleGridDebtSummary totals={totals} />
            {debts.length > 0 && (
              <Box overflowX="auto" mb={4}>
                <Table size="sm">
                  <Thead>
                    <Tr>
                      <Th>Omschrijving</Th>
                      <Th isNumeric>Saldo</Th>
                      <Th isNumeric>Rente YTD</Th>
                      <Th />
                    </Tr>
                  </Thead>
                  <Tbody>
                    {debts.map((d) => (
                      <Tr key={d.id}>
                        <Td>{d.label}</Td>
                        <Td isNumeric>{formatEur(d.outstanding_eur)}</Td>
                        <Td isNumeric>{formatEur(d.interest_paid_ytd_eur)}</Td>
                        <Td>
                          <Button size="xs" variant="ghost" isDisabled={busy} onClick={() => void handleDeleteDebt(d.id)}>
                            Verwijder
                          </Button>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
            )}
            <FiscalCard elevated p={5}>
              <Text fontWeight={600} mb={4}>Schuld toevoegen</Text>
              <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={3}>
                <FormControl isRequired>
                  <FormLabel fontSize="sm">Omschrijving</FormLabel>
                  <Input {...inputSx} value={debtLabel} onChange={(e) => setDebtLabel(e.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Type</FormLabel>
                  <Select size="sm" value={debtType} onChange={(e) => setDebtType(e.target.value)}>
                    {DEBT_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </Select>
                </FormControl>
                <FormControl isRequired>
                  <FormLabel fontSize="sm">Uitstaand (€)</FormLabel>
                  <Input {...inputSx} inputMode="decimal" value={debtOutstanding} onChange={(e) => setDebtOutstanding(e.target.value)} />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Betaalde rente YTD (€)</FormLabel>
                  <Input {...inputSx} inputMode="decimal" value={debtInterest} onChange={(e) => setDebtInterest(e.target.value)} />
                </FormControl>
              </Grid>
              <Button variant="fiscal" size="sm" mt={4} isLoading={busy} onClick={() => void handleAddDebt()}>
                + Schuld toevoegen
              </Button>
              {debtError && <Text fontSize="sm" color="rust.500" mt={2}>{debtError}</Text>}
            </FiscalCard>
          </TabPanel>

          <TabPanel px={0}>
            {banks.map((b) => (
              <FiscalCard key={b.id} elevated p={4} mb={3}>
                <Flex justify="space-between">
                  <Box>
                    <Text fontWeight={600}>{b.label}</Text>
                    <Text fontSize="sm" color="ink.dim">{formatEur(b.balance_eur)}</Text>
                  </Box>
                  <Button size="sm" variant="fiscalOutline" color="rust.500" isDisabled={busy} onClick={() => void handleDeleteBank(b.id)}>
                    Verwijderen
                  </Button>
                </Flex>
              </FiscalCard>
            ))}
            <FiscalCard elevated p={5}>
              <Text fontWeight={600} mb={4}>Banktegoed toevoegen</Text>
              <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={3}>
                <FormControl isRequired>
                  <FormLabel fontSize="sm">Omschrijving</FormLabel>
                  <Input {...inputSx} value={bankLabel} onChange={(e) => setBankLabel(e.target.value)} placeholder="ING Spaarrekening" />
                </FormControl>
                <FormControl>
                  <FormLabel fontSize="sm">Type</FormLabel>
                  <Select size="sm" value={bankType} onChange={(e) => setBankType(e.target.value)}>
                    {BANK_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </Select>
                </FormControl>
                <FormControl isRequired>
                  <FormLabel fontSize="sm">Saldo peildatum (€)</FormLabel>
                  <Input {...inputSx} inputMode="decimal" value={bankBalance} onChange={(e) => setBankBalance(e.target.value)} />
                </FormControl>
              </Grid>
              <Button variant="fiscal" size="sm" mt={4} isLoading={busy} onClick={() => void handleAddBank()}>
                + Banktegoed toevoegen
              </Button>
              {bankError && <Text fontSize="sm" color="rust.500" mt={2}>{bankError}</Text>}
            </FiscalCard>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </VStack>
  );
}

function SimpleGridDebtSummary({
  totals,
}: {
  totals: { debtTotal: number; threshold: number; debtDeductible: number };
}) {
  return (
    <StatStrip
      columns={3}
      items={[
        { label: "Totale box 3-schulden", value: formatEur(String(totals.debtTotal)), sub: "excl. hypotheek eigen woning", tone: "ochre" },
        { label: "Drempel", value: formatEur(String(totals.threshold)), sub: "per persoon / fiscaal partner" },
        { label: "Verlaagt vermogen met", value: formatEur(String(totals.debtDeductible)), sub: "schuld boven drempel", tone: "moss" },
      ]}
    />
  );
}
