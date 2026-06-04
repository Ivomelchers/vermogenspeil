"""DEGIRO Transactions-export — kolomschema v1 (uitgebreide aliases)."""

from apps.integrations.csv.column_schema import ColumnField, PlatformColumnSchema

# Aliases afgeleid van officiële DEGIRO-export + veelvoorkomende varianten/typos in
# andere tools (PP/Ghostfolio). Uitbreiden na report_csv_drift of echte bètatester-export.
DEGIRO_SCHEMA = PlatformColumnSchema(
    platform="degiro",
    schema_version="degiro-transactions-v3",
    fields=(
        ColumnField(
            "date",
            "Date",
            frozenset({"date", "datum", "trade date", "tradedate", "boekdatum"}),
            required=True,
        ),
        ColumnField("time", "Time", frozenset({"time", "tijd", "hour"})),
        ColumnField("product", "Product", frozenset({"product", "security", "name"})),
        ColumnField("isin", "ISIN", frozenset({"isin", "symbol", "ticker"})),
        ColumnField(
            "mic",
            "MIC",
            frozenset({"uitvoeringsplaats", "mic", "exchange", "exchange code"}),
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
            frozenset({"currency", "ccy", "munt", "fx"}),
        ),
        ColumnField(
            "quantity",
            "Quantity",
            frozenset({"quantity", "aantal", "qty", "amount shares", "stuks"}),
        ),
        ColumnField(
            "price",
            "Price",
            frozenset({"price", "koers", "unit price", "share price", "prijs"}),
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
            frozenset({"order id", "orderid", "order-id", "order nr"}),
            fingerprint=False,
            required=False,
        ),
        ColumnField(
            "local_value",
            "Local value",
            frozenset({"local value", "lokale waarde", "value local"}),
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
