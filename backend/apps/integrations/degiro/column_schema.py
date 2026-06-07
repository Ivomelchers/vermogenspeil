"""DEGIRO Transactions-export — kolomschema v1 (uitgebreide aliases)."""

from apps.integrations.csv.column_schema import ColumnField, PlatformColumnSchema

# Aliases afgeleid van officiële DEGIRO-export + veelvoorkomende varianten/typos in
# andere tools (PP/Ghostfolio). Uitbreiden na report_csv_drift of echte bètatester-export.
DEGIRO_SCHEMA = PlatformColumnSchema(
    platform="degiro",
    schema_version="degiro-transactions-v4",
    fields=(
        ColumnField(
            "date",
            "Date",
            frozenset(
                {
                    "date",
                    "datum",
                    "trade date",
                    "tradedate",
                    "boekdatum",
                    "booking date now",
                    "when traded",
                    "trade day",
                    "settlement date",
                }
            ),
            required=True,
        ),
        ColumnField(
            "time",
            "Time",
            frozenset(
                {"time", "tijd", "hour", "clock", "clock time", "execution time"}
            ),
        ),
        ColumnField(
            "product",
            "Product",
            frozenset(
                {
                    "product",
                    "security",
                    "name",
                    "instrument",
                    "inst",
                    "inst name",
                    "security label",
                }
            ),
        ),
        ColumnField(
            "isin",
            "ISIN",
            frozenset(
                {"isin", "symbol", "ticker", "isin id", "isin code", "identifier isin"}
            ),
        ),
        ColumnField(
            "mic",
            "MIC",
            frozenset(
                {
                    "uitvoeringsplaats",
                    "mic",
                    "exchange",
                    "exchange code",
                    "exec venue",
                    "market",
                    "trading floor",
                }
            ),
            required=False,
            fingerprint=False,
        ),
        ColumnField(
            "description",
            "Description",
            frozenset(
                {
                    "description",
                    "omschrijving",
                    "type",
                    "transaction type",
                    "action",
                    "soort",
                }
            ),
            required=False,
            fingerprint=False,
        ),
        ColumnField(
            "currency",
            "Currency",
            frozenset({"currency", "ccy", "munt", "fx", "fx ccy", "currency pair"}),
        ),
        ColumnField(
            "quantity",
            "Quantity",
            frozenset(
                {
                    "quantity",
                    "aantal",
                    "qty",
                    "amount shares",
                    "stuks",
                    "shares",
                    "qty shares",
                    "share qty",
                    "units held",
                }
            ),
        ),
        ColumnField(
            "price",
            "Price",
            frozenset(
                {
                    "price",
                    "koers",
                    "unit price",
                    "share price",
                    "prijs",
                    "px",
                    "unit px",
                    "price per unit",
                }
            ),
        ),
        ColumnField(
            "fee",
            "Transaction costs",
            frozenset(
                {
                    "transaction costs",
                    "transactiekosten",
                    "transactiekosten en/of kosten van derden eur",
                    "kosten",
                    "fees",
                    "fee",
                    "commission",
                    "provisie",
                    "charges",
                    "autofx kosten",
                    "costs eur",
                    "costs",
                    "fee costs",
                    "broker fee",
                    "conversion charge",
                }
            ),
        ),
        ColumnField(
            "total",
            "Total",
            frozenset(
                {
                    "total",
                    "totaal",
                    "totaal eur",
                    "sum eur",
                    "net sum",
                    "settle total",
                    "net settlement",
                    "value",
                    "subtotal",
                    "sub total",
                    "sub-total",
                    "amount",
                    "bedrag",
                    "net amount",
                    "gross amount",
                    "mutation",
                    "mutatie",
                    "change",
                    "nettowaarde",
                }
            ),
            # NL-export heeft óók "Waarde EUR" — dat is géén afschrijfbedrag (zie local_value).
        ),
        ColumnField(
            "order_id",
            "Order ID",
            frozenset(
                {
                    "order id",
                    "orderid",
                    "order-id",
                    "order nr",
                    "ref",
                    "ref no",
                    "order ref",
                    "ticket id",
                }
            ),
            fingerprint=False,
            required=False,
        ),
        ColumnField(
            "local_value",
            "Local value",
            frozenset(
                {"local value", "lokale waarde", "value local", "local val", "amount local"}
            ),
            fingerprint=False,
        ),
        ColumnField(
            "exchange_rate",
            "Exchange rate",
            frozenset({"exchange rate", "wisselkoers", "fx rate"}),
            fingerprint=False,
        ),
    ),
)
