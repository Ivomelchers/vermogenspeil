"""Map Bybit v5 execution items naar TradeRecord."""

from datetime import datetime, timezone as dt_timezone
from decimal import Decimal, InvalidOperation

from apps.integrations.base import TradeRecord
from apps.portfolio.models import AssetType, TransactionType

CASH_SYMBOLS = frozenset({"EUR", "USD", "USDT", "USDC"})

_QUOTE_SUFFIXES = ("USDT", "USDC", "EUR", "USD", "BTC", "ETH")


def _parse_decimal(value) -> Decimal:
    if value is None or value == "":
        return Decimal(0)
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return Decimal(0)


def base_symbol_from_pair(symbol: str) -> str:
    raw = (symbol or "").strip().upper()
    if not raw:
        return raw
    if "-" in raw:
        return raw.split("-")[0]
    if "/" in raw:
        return raw.split("/")[0]
    for quote in _QUOTE_SUFFIXES:
        if raw.endswith(quote) and len(raw) > len(quote):
            return raw[: -len(quote)]
    return raw


def parse_exec_time(value) -> datetime:
    if value is None:
        return datetime.now(tz=dt_timezone.utc)
    text = str(value).strip()
    if text.isdigit():
        ms = int(text)
        return datetime.fromtimestamp(ms / 1000, tz=dt_timezone.utc)
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now(tz=dt_timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt_timezone.utc)
    return parsed.astimezone(dt_timezone.utc)


def map_bybit_side(side: str) -> str:
    normalized = (side or "").lower()
    if normalized in ("sell", "s"):
        return TransactionType.SELL
    return TransactionType.BUY


def execution_to_trade_record(item: dict) -> TradeRecord | None:
    symbol_raw = item.get("symbol") or item.get("symbolName") or ""
    base = base_symbol_from_pair(symbol_raw)
    if not base:
        return None

    quantity = abs(_parse_decimal(item.get("execQty") or item.get("orderQty")))
    price = abs(_parse_decimal(item.get("execPrice") or item.get("avgPrice")))
    if quantity <= 0:
        return None

    side = map_bybit_side(item.get("side", ""))
    fee = abs(_parse_decimal(item.get("execFee") or item.get("fee")))
    occurred_at = parse_exec_time(item.get("execTime") or item.get("createdTime"))
    external_id = item.get("execId") or item.get("orderId") or ""

    asset_type = AssetType.CASH if base in CASH_SYMBOLS else AssetType.CRYPTO

    return TradeRecord(
        external_id=str(external_id),
        symbol=base,
        side=(item.get("side") or "").lower(),
        quantity=quantity,
        price_eur=price,
        fee_eur=fee,
        occurred_at=occurred_at,
        market=symbol_raw,
        asset_type=asset_type,
        transaction_type=side,
        total_eur=quantity * price,
    )
