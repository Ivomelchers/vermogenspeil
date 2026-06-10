"""OKX trading history export — kolomschema."""

from apps.integrations.csv.column_schema import ColumnField, PlatformColumnSchema

OKX_SCHEMA = PlatformColumnSchema(
    platform="okx",
    schema_version="okx-spot-trades-v1",
    fields=(
        ColumnField(
            "symbol",
            "instId",
            frozenset({"instid", "inst id", "symbol", "instrument", "pair"}),
            required=True,
        ),
        ColumnField(
            "side",
            "side",
            frozenset({"side", "direction", "type", "order side"}),
            required=True,
        ),
        ColumnField(
            "quantity",
            "fillSz",
            frozenset({"fillsz", "fill sz", "size", "quantity", "qty", "filled size"}),
            required=True,
        ),
        ColumnField(
            "price",
            "fillPx",
            frozenset({"fillpx", "fill px", "price", "fill price", "avg price"}),
            required=True,
        ),
        ColumnField(
            "fee",
            "fee",
            frozenset({"fee", "fees", "commission", "trading fee"}),
        ),
        ColumnField(
            "executed_at",
            "ts",
            frozenset({"ts", "time", "timestamp", "trade time", "fill time"}),
            required=True,
        ),
        ColumnField(
            "trade_id",
            "tradeId",
            frozenset({"tradeid", "trade id", "id", "bill id", "billid"}),
            fingerprint=False,
            required=False,
        ),
    ),
)
