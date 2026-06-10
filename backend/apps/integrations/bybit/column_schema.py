"""Bybit spot trade export — kolomschema."""

from apps.integrations.csv.column_schema import ColumnField, PlatformColumnSchema

BYBIT_SCHEMA = PlatformColumnSchema(
    platform="bybit",
    schema_version="bybit-spot-trades-v1",
    fields=(
        ColumnField(
            "symbol",
            "Symbol",
            frozenset({"symbol", "pair", "market", "trading pair"}),
            required=True,
        ),
        ColumnField(
            "side",
            "Side",
            frozenset({"side", "direction", "type", "order side"}),
            required=True,
        ),
        ColumnField(
            "quantity",
            "Filled Qty",
            frozenset(
                {
                    "filled qty",
                    "filled quantity",
                    "execqty",
                    "exec qty",
                    "quantity",
                    "qty",
                    "filled",
                }
            ),
            required=True,
        ),
        ColumnField(
            "price",
            "Avg. Filled Price",
            frozenset(
                {
                    "avg. filled price",
                    "avg filled price",
                    "execprice",
                    "exec price",
                    "price",
                    "avg price",
                    "filled price",
                }
            ),
            required=True,
        ),
        ColumnField(
            "fee",
            "Trading Fees",
            frozenset(
                {
                    "trading fees",
                    "fee",
                    "fees",
                    "trading fee",
                    "commission",
                }
            ),
        ),
        ColumnField(
            "order_id",
            "Order No.",
            frozenset(
                {
                    "order no.",
                    "order no",
                    "orderid",
                    "order id",
                    "order number",
                }
            ),
            fingerprint=False,
            required=False,
        ),
        ColumnField(
            "executed_at",
            "Transaction Time",
            frozenset(
                {
                    "transaction time",
                    "exectime",
                    "exec time",
                    "time",
                    "timestamp",
                    "trade time",
                }
            ),
            required=True,
        ),
    ),
)
