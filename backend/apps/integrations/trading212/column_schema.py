"""Trading 212 activity-export — kolomschema v1."""

from apps.integrations.csv.column_schema import ColumnField, PlatformColumnSchema

TRADING212_SCHEMA = PlatformColumnSchema(
    platform="trading212",
    schema_version="trading212-activity-v1",
    fields=(
        ColumnField(
            "action",
            "Action",
            frozenset({"action", "type", "transaction type", "activity type"}),
            required=True,
        ),
        ColumnField(
            "time",
            "Time",
            frozenset({"time", "timestamp", "date", "datetime", "date time"}),
            required=True,
        ),
        ColumnField(
            "isin",
            "ISIN",
            frozenset({"isin", "isin code", "identifier"}),
        ),
        ColumnField(
            "ticker",
            "Ticker",
            frozenset({"ticker", "symbol", "ticker symbol"}),
            fingerprint=False,
        ),
        ColumnField(
            "name",
            "Name",
            frozenset({"name", "instrument", "product", "security"}),
            fingerprint=False,
        ),
        ColumnField(
            "id",
            "ID",
            frozenset({"id", "transaction id", "order id", "reference"}),
            fingerprint=False,
            required=False,
        ),
        ColumnField(
            "quantity",
            "No. of shares",
            frozenset(
                {
                    "no. of shares",
                    "no of shares",
                    "number of shares",
                    "shares",
                    "quantity",
                    "qty",
                }
            ),
        ),
        ColumnField(
            "price",
            "Price / share",
            frozenset(
                {
                    "price / share",
                    "price/share",
                    "price per share",
                    "share price",
                    "price",
                    "rate",
                }
            ),
        ),
        ColumnField(
            "total",
            "Total",
            frozenset({"total", "amount", "value", "total amount"}),
            required=True,
        ),
        ColumnField(
            "currency_total",
            "Currency (Total)",
            frozenset(
                {
                    "currency (total)",
                    "currency total",
                    "total currency",
                    "currency",
                }
            ),
            fingerprint=False,
        ),
        ColumnField(
            "result",
            "Result",
            frozenset({"result", "profit", "p/l", "pnl", "realized pnl"}),
            fingerprint=False,
        ),
        ColumnField(
            "currency_result",
            "Currency (Result)",
            frozenset({"currency (result)", "currency result", "result currency"}),
            fingerprint=False,
        ),
    ),
)
