"""Trade Republic transactie-export — kolomschema v1."""

from apps.integrations.csv.column_schema import ColumnField, PlatformColumnSchema

TRADE_REPUBLIC_SCHEMA = PlatformColumnSchema(
    platform="trade_republic",
    schema_version="trade-republic-transactions-v1",
    fields=(
        ColumnField(
            "id",
            "ID",
            frozenset({"id", "transaction id", "uuid"}),
            required=True,
        ),
        ColumnField(
            "status",
            "Status",
            frozenset({"status", "state"}),
            fingerprint=False,
        ),
        ColumnField(
            "timestamp",
            "Timestamp",
            frozenset({"timestamp", "time", "date", "datetime"}),
            required=True,
        ),
        ColumnField(
            "type",
            "Type",
            frozenset({"type", "transaction type", "activity type"}),
            required=True,
        ),
        ColumnField(
            "asset_type",
            "Asset type",
            frozenset({"asset type", "assettype", "asset class"}),
            fingerprint=False,
        ),
        ColumnField(
            "name",
            "Name",
            frozenset({"name", "instrument name", "product", "security"}),
            fingerprint=False,
        ),
        ColumnField(
            "instrument",
            "Instrument",
            frozenset({"instrument", "isin", "symbol", "ticker"}),
        ),
        ColumnField(
            "shares",
            "Shares",
            frozenset({"shares", "quantity", "qty", "amount shares"}),
        ),
        ColumnField(
            "rate",
            "Rate",
            frozenset({"rate", "price", "price per share", "share price"}),
        ),
        ColumnField(
            "commission",
            "Commission",
            frozenset({"commission", "fee", "fees", "provisie"}),
            fingerprint=False,
        ),
        ColumnField(
            "debit",
            "Debit",
            frozenset({"debit", "debited", "outflow"}),
        ),
        ColumnField(
            "credit",
            "Credit",
            frozenset({"credit", "credited", "inflow"}),
        ),
        ColumnField(
            "tax_amount",
            "Tax amount",
            frozenset({"tax amount", "tax", "withholding tax", "belasting"}),
            fingerprint=False,
        ),
    ),
)
