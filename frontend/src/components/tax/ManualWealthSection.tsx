import { useCallback, useEffect, useState } from "react";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Grid,
  Input,
  Select,
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
import FiscalCard from "../common/FiscalCard";
import Kicker from "../common/Kicker";
import { formatEur } from "../../utils/formatMoney";
import { getApiErrorMessage } from "../../utils/apiError";

const BANK_TYPES: { value: string; label: string }[] = [
  { value: "savings", label: "Spaarrekening" },
  { value: "checking", label: "Betaalrekening" },
  { value: "deposit", label: "Depositorekening" },
  { value: "other", label: "Overig banktegoed" },
];

const DEBT_TYPES: { value: string; label: string }[] = [
  { value: "consumer", label: "Consumptief" },
  { value: "investment", label: "Beleggingsfinanciering" },
  { value: "mortgage_second_home", label: "Hypotheek 2e woning" },
  { value: "negative_balance", label: "Negatief banksaldo" },
  { value: "other", label: "Overig" },
];

const PROPERTY_TYPES: { value: string; label: string }[] = [
  { value: "second_home_nl", label: "2e woning NL" },
  { value: "second_home_abroad", label: "2e woning buitenland" },
  { value: "rental_nl", label: "Verhuurd NL" },
  { value: "rental_abroad", label: "Verhuurd buitenland" },
  { value: "other", label: "Overig onroerend" },
];

interface ManualWealthSectionProps {
  taxYear: number;
  onChanged?: () => void;
}

export default function ManualWealthSection({ taxYear, onChanged }: ManualWealthSectionProps) {
  const [banks, setBanks] = useState<Box3BankBalance[]>([]);
  const [debts, setDebts] = useState<Box3Debt[]>([]);
  const [properties, setProperties] = useState<Box3RealEstate[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
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

  const [propLabel, setPropLabel] = useState("");
  const [propType, setPropType] = useState("second_home_nl");
  const [propValue, setPropValue] = useState("");
  const [propRentYtd, setPropRentYtd] = useState("0");
  const [propWoz, setPropWoz] = useState("");
  const [propEigenDays, setPropEigenDays] = useState("365");
  const [propBijtelling, setPropBijtelling] = useState("woz_vast");

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
      setLoadError(getApiErrorMessage(err, "Handmatig vermogen laden mislukt."));
    } finally {
      setLoading(false);
    }
  }, [taxYear]);

  useEffect(() => {
    void load();
  }, [load]);

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
      onChanged?.();
    } catch (createError) {
      setBankError(getApiErrorMessage(createError, "Banktegoed toevoegen mislukt."));
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
      onChanged?.();
    } catch (deleteError) {
      setBankError(getApiErrorMessage(deleteError, "Verwijderen mislukt."));
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
        linked_real_estate: null,
        notes: "",
      });
      setDebtLabel("");
      setDebtOutstanding("");
      setDebtInterest("0");
      await load();
      onChanged?.();
    } catch (createError) {
      setDebtError(getApiErrorMessage(createError, "Schuld toevoegen mislukt."));
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
        annual_rent_eur: "0",
        vacancy_ratio: "0",
        rental_income_ytd_eur: propRentYtd.replace(",", ".") || "0",
        eigen_gebruik_days: Number(propEigenDays) || 0,
        verhuur_days: 0,
        verbouw_days: 0,
        bijtelling_method: propBijtelling,
        economic_rent_yearly_eur: "0",
        woz_previous_year_eur: propWoz.replace(",", ".") || propValue.replace(",", "."),
        bijtelling_rate: "0.0275",
        notes: "",
      });
      setPropLabel("");
      setPropValue("");
      setPropRentYtd("0");
      setPropWoz("");
      await load();
      onChanged?.();
    } catch (createError) {
      setPropertyError(getApiErrorMessage(createError, "Vastgoed toevoegen mislukt."));
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
      onChanged?.();
    } catch (deleteError) {
      setDebtError(getApiErrorMessage(deleteError, "Verwijderen mislukt."));
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
      onChanged?.();
    } catch (deleteError) {
      setPropertyError(getApiErrorMessage(deleteError, "Verwijderen mislukt."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <VStack align="stretch" spacing={4}>
      <FiscalCard p={5}>
        <Kicker mb={2}>Banktegoeden (Box 3 · B)</Kicker>
        <Text color="ink.dim" fontSize="sm" mb={4} lineHeight={1.7}>
          Spaar- en betaalrekeningen op peildatum 1 januari. Telt mee in forfaitair rendement op
          banktegoeden.
        </Text>
        {loading ? (
          <Text color="ink.dim" fontSize="sm">
            Laden…
          </Text>
        ) : (
          <>
            {banks.length > 0 && (
              <Box overflowX="auto" mb={4}>
                <Table size="sm">
                  <Thead>
                    <Tr>
                      <Th>Omschrijving</Th>
                      <Th isNumeric>Saldo</Th>
                      <Th />
                    </Tr>
                  </Thead>
                  <Tbody>
                    {banks.map((b) => (
                      <Tr key={b.id}>
                        <Td>{b.label}</Td>
                        <Td isNumeric>{formatEur(b.balance_eur)}</Td>
                        <Td>
                          <Button
                            size="xs"
                            variant="ghost"
                            isDisabled={busy}
                            onClick={() => void handleDeleteBank(b.id)}
                          >
                            Verwijder
                          </Button>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
            )}
            <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={3}>
              <FormControl>
                <FormLabel fontSize="sm">Omschrijving</FormLabel>
                <Input
                  size="sm"
                  value={bankLabel}
                  onChange={(e) => setBankLabel(e.target.value)}
                  placeholder="bijv. ING Spaar"
                />
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">Type</FormLabel>
                <Select size="sm" value={bankType} onChange={(e) => setBankType(e.target.value)}>
                  {BANK_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">Saldo peildatum (€)</FormLabel>
                <Input
                  size="sm"
                  inputMode="decimal"
                  value={bankBalance}
                  onChange={(e) => setBankBalance(e.target.value)}
                />
              </FormControl>
            </Grid>
            <Button
              variant="fiscalOutline"
              size="sm"
              mt={3}
              isLoading={busy}
              onClick={() => void handleAddBank()}
            >
              Banktegoed toevoegen
            </Button>
            {bankError && (
              <Text fontSize="sm" color="red.500" mt={2}>
                {bankError}
              </Text>
            )}
          </>
        )}
      </FiscalCard>

      <FiscalCard p={5}>
        <Kicker mb={2}>Schulden (Box 3)</Kicker>
        <Text color="ink.dim" fontSize="sm" mb={4} lineHeight={1.7}>
          Schulden tellen mee in forfaitair (S) en in werkelijk rendement als rente (RNT_s).
        </Text>
        {loading ? (
          <Text color="ink.dim" fontSize="sm">
            Laden…
          </Text>
        ) : (
          <>
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
                          <Button
                            size="xs"
                            variant="ghost"
                            isDisabled={busy}
                            onClick={() => void handleDeleteDebt(d.id)}
                          >
                            Verwijder
                          </Button>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>
            )}
            <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={3}>
              <FormControl>
                <FormLabel fontSize="sm">Omschrijving</FormLabel>
                <Input size="sm" value={debtLabel} onChange={(e) => setDebtLabel(e.target.value)} />
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">Type</FormLabel>
                <Select size="sm" value={debtType} onChange={(e) => setDebtType(e.target.value)}>
                  {DEBT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">Uitstaand (€)</FormLabel>
                <Input
                  size="sm"
                  inputMode="decimal"
                  value={debtOutstanding}
                  onChange={(e) => setDebtOutstanding(e.target.value)}
                />
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">Betaalde rente YTD (€)</FormLabel>
                <Input
                  size="sm"
                  inputMode="decimal"
                  value={debtInterest}
                  onChange={(e) => setDebtInterest(e.target.value)}
                />
              </FormControl>
            </Grid>
            <Button
              variant="fiscalOutline"
              size="sm"
              mt={3}
              isLoading={busy}
              onClick={() => void handleAddDebt()}
            >
              Schuld toevoegen
            </Button>
            {debtError && (
              <Text fontSize="sm" color="red.500" mt={2}>
                {debtError}
              </Text>
            )}
          </>
        )}
      </FiscalCard>

      <FiscalCard p={5}>
        <Kicker mb={2}>Vastgoed (Box 3)</Kicker>
        <Text color="ink.dim" fontSize="sm" mb={4} lineHeight={1.7}>
          Waarde telt mee als overige bezittingen; bijtelling (eigen gebruik) en huur voor werkelijk
          rendement.
        </Text>
        {properties.length > 0 && (
          <Box overflowX="auto" mb={4}>
            <Table size="sm">
              <Thead>
                <Tr>
                  <Th>Omschrijving</Th>
                  <Th isNumeric>Waarde</Th>
                  <Th isNumeric>Huur YTD</Th>
                  <Th />
                </Tr>
              </Thead>
              <Tbody>
                {properties.map((p) => (
                  <Tr key={p.id}>
                    <Td>{p.label}</Td>
                    <Td isNumeric>{formatEur(p.value_eur)}</Td>
                    <Td isNumeric>{formatEur(p.rental_income_ytd_eur)}</Td>
                    <Td>
                      <Button
                        size="xs"
                        variant="ghost"
                        isDisabled={busy}
                        onClick={() => void handleDeleteProperty(p.id)}
                      >
                        Verwijder
                      </Button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
        )}
        <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={3}>
          <FormControl>
            <FormLabel fontSize="sm">Omschrijving</FormLabel>
            <Input size="sm" value={propLabel} onChange={(e) => setPropLabel(e.target.value)} />
          </FormControl>
          <FormControl>
            <FormLabel fontSize="sm">Type</FormLabel>
            <Select size="sm" value={propType} onChange={(e) => setPropType(e.target.value)}>
              {PROPERTY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </Select>
          </FormControl>
          <FormControl>
            <FormLabel fontSize="sm">Waarde peildatum (€)</FormLabel>
            <Input
              size="sm"
              inputMode="decimal"
              value={propValue}
              onChange={(e) => setPropValue(e.target.value)}
            />
          </FormControl>
          <FormControl>
            <FormLabel fontSize="sm">WOZ vorig jaar (€, bijtelling)</FormLabel>
            <Input
              size="sm"
              inputMode="decimal"
              value={propWoz}
              onChange={(e) => setPropWoz(e.target.value)}
            />
          </FormControl>
          <FormControl>
            <FormLabel fontSize="sm">Eigen gebruik (dagen)</FormLabel>
            <Input
              size="sm"
              inputMode="numeric"
              value={propEigenDays}
              onChange={(e) => setPropEigenDays(e.target.value)}
            />
          </FormControl>
          <FormControl>
            <FormLabel fontSize="sm">Bijtelling</FormLabel>
            <Select
              size="sm"
              value={propBijtelling}
              onChange={(e) => setPropBijtelling(e.target.value)}
            >
              <option value="woz_vast">Vast % WOZ</option>
              <option value="huurwaarde">Economische huurwaarde</option>
            </Select>
          </FormControl>
          <FormControl>
            <FormLabel fontSize="sm">Huurinkomsten YTD (€)</FormLabel>
            <Input
              size="sm"
              inputMode="decimal"
              value={propRentYtd}
              onChange={(e) => setPropRentYtd(e.target.value)}
            />
          </FormControl>
        </Grid>
        <Button
          variant="fiscalOutline"
          size="sm"
          mt={3}
          isLoading={busy}
          onClick={() => void handleAddProperty()}
        >
          Vastgoed toevoegen
        </Button>
        {propertyError && (
          <Text fontSize="sm" color="red.500" mt={2}>
            {propertyError}
          </Text>
        )}
      </FiscalCard>

      {loadError && (
        <Text fontSize="sm" color="red.500">
          {loadError}
        </Text>
      )}
    </VStack>
  );
}
