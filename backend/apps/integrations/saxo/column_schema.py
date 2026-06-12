"""Saxo Bank CSV column schema."""

from apps.integrations.csv.column_schema import ColumnField, PlatformColumnSchema

SAXO_SCHEMA = PlatformColumnSchema(
    platform="saxo",
    schema_version="saxo-v1",
    fields=(
        ColumnField(
            "date",
            "Date",
            frozenset(
                {
                    "date",
                    "dato",
                    "execution date",
                    "executed date",
                    "trade date",
                    "datum",
                }
            ),
            required=True,
        ),
        ColumnField(
            "time",
            "Time",
            frozenset(
                {
                    "time",
                    "tid",
                    "execution time",
                    "trade time",
                }
            ),
        ),
        ColumnField(
            "symbol",
            "Symbol",
            frozenset(
                {
                    "symbol",
                    "ticker",
                    "instrument",
                    "handle",
                    "isin",
                }
            ),
            required=True,
        ),
        ColumnField(
            "description",
            "Description",
            frozenset(
                {
                    "description",
                    "navn",
                    "name",
                    "asset name",
                    "instrument name",
                }
            ),
        ),
        ColumnField(
            "type",
            "Transaction Type",
            frozenset(
                {
                    "type",
                    "transactiontype",
                    "transaction type",
                    "type af handel",
                    "side",
                    "buysell",
                }
            ),
            required=True,
        ),
        ColumnField(
            "quantity",
            "Quantity",
            frozenset(
                {
                    "quantity",
                    "qty",
                    "amount",
                    "antal",
                    "mængde",
                }
            ),
            required=True,
        ),
        ColumnField(
            "price",
            "Price",
            frozenset(
                {
                    "price",
                    "kurs",
                    "course",
                    "price per unit",
                    "price eur",
                }
            ),
        ),
        ColumnField(
            "total",
            "Total",
            frozenset(
                {
                    "total",
                    "beløb",
                    "total amount",
                    "value",
                    "total eur",
                }
            ),
        ),
        ColumnField(
            "fees",
            "Fees",
            frozenset(
                {
                    "fees",
                    "costs",
                    "gebühren",
                    "commission",
                    "fee eur",
                    "cost",
                    "gebyr",
                }
            ),
        ),
        ColumnField(
            "isin",
            "ISIN",
            frozenset(
                {
                    "isin",
                    "security id",
                    "id",
                }
            ),
        ),
        ColumnField(
            "currency",
            "Currency",
            frozenset(
                {
                    "currency",
                    "valuta",
                    "mønt",
                }
            ),
        ),
    ),
)
