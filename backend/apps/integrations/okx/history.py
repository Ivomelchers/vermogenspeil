"""Map OKX v5 fill items naar TradeRecord."""

from datetime import datetime, timezone as dt_timezone
from decimal import Decimal, InvalidOperation

from apps.integrations.base import TradeRecord
from apps.integrations.bybit.history import base_symbol_from_pair, CASH_SYMBOLS
from apps.portfolio.models import AssetType, TransactionType


def _parse_decimal(value) -> Decimal:
    if value is None or value == "":
        return Decimal(0)
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return Decimal(0)


def parse_fill_time(value) -> datetime:
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


def map_okx_side(side: str) -> str:
    normalized = (side or "").lower()
    if normalized in ("sell", "s"):
        return TransactionType.SELL
    return TransactionType.BUY


def fill_to_trade_record(item: dict) -> TradeRecord | None:
    symbol_raw = item.get("instId") or item.get("symbol") or ""
    base = base_symbol_from_pair(symbol_raw)
    if not base:
        return None

    quantity = abs(_parse_decimal(item.get("fillSz") or item.get("sz")))
    price = abs(_parse_decimal(item.get("fillPx") or item.get("px")))
    if quantity <= 0:
        return None

    side = map_okx_side(item.get("side", ""))
    fee = abs(_parse_decimal(item.get("fee")))
    occurred_at = parse_fill_time(item.get("ts") or item.get("fillTime"))
    external_id = item.get("tradeId") or item.get("billId") or ""

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
