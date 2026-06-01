"""Map Bitvavo GET /account/history items naar TradeRecord."""

from datetime import datetime, timezone as dt_timezone
from decimal import Decimal, InvalidOperation

from apps.integrations.base import TradeRecord
from apps.portfolio.models import AssetType, TransactionType

CASH_SYMBOL = "EUR"

_BITVAVO_TYPE_MAP: dict[str, str] = {
    "buy": TransactionType.BUY,
    "sell": TransactionType.SELL,
    "deposit": TransactionType.DEPOSIT,
    "withdrawal": TransactionType.WITHDRAWAL,
    "staking": TransactionType.OTHER,
    "fixed_staking": TransactionType.OTHER,
    "affiliate": TransactionType.OTHER,
    "distribution": TransactionType.DIVIDEND,
    "internal_transfer": TransactionType.OTHER,
    "withdrawal_cancelled": TransactionType.OTHER,
    "rebate": TransactionType.OTHER,
    "loan": TransactionType.OTHER,
    "external_transferred_funds": TransactionType.DEPOSIT,
    "manually_assigned": TransactionType.OTHER,
    "manually_assigned_bitvavo": TransactionType.OTHER,
}


def map_bitvavo_history_type(bitvavo_type: str) -> str:
    return _BITVAVO_TYPE_MAP.get((bitvavo_type or "").lower(), TransactionType.OTHER)


def _parse_decimal(value) -> Decimal:
    if value is None or value == "":
        return Decimal(0)
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return Decimal(0)


def parse_executed_at(value) -> datetime:
    if value is None:
        return datetime.now(tz=dt_timezone.utc)
    if isinstance(value, (int, float)):
        ms = int(value)
        return datetime.fromtimestamp(ms / 1000, tz=dt_timezone.utc)
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


def _primary_symbol(item: dict, tx_type: str) -> tuple[str, str]:
    """Return (symbol, asset_type) for the transaction asset."""
    received = (item.get("receivedCurrency") or "").strip()
    sent = (item.get("sentCurrency") or "").strip()

    if tx_type in (TransactionType.DEPOSIT, TransactionType.WITHDRAWAL):
        return CASH_SYMBOL, AssetType.CASH

    if tx_type == TransactionType.BUY:
        symbol = received or sent or CASH_SYMBOL
    elif tx_type == TransactionType.SELL:
        symbol = sent or received or CASH_SYMBOL
    else:
        symbol = received or sent or CASH_SYMBOL

    if symbol == CASH_SYMBOL:
        return symbol, AssetType.CASH
    return symbol, AssetType.CRYPTO


def _quantity_and_price(item: dict, tx_type: str) -> tuple[Decimal, Decimal | None, Decimal]:
    price_amount = abs(_parse_decimal(item.get("priceAmount")))
    received_amount = abs(_parse_decimal(item.get("receivedAmount")))
    sent_amount = abs(_parse_decimal(item.get("sentAmount")))
    fee = abs(_parse_decimal(item.get("feesAmount")))

    if tx_type == TransactionType.BUY:
        quantity = received_amount or sent_amount
        total = price_amount or quantity * _parse_decimal(item.get("price")) if quantity else Decimal(0)
        price = (total / quantity) if quantity else None
        return quantity or Decimal(1), price, total or Decimal(0)

    if tx_type == TransactionType.SELL:
        quantity = sent_amount or received_amount
        total = price_amount or quantity
        price = (total / quantity) if quantity else None
        return quantity or Decimal(1), price, total or Decimal(0)

    if tx_type in (TransactionType.DEPOSIT, TransactionType.WITHDRAWAL):
        total = price_amount or received_amount or sent_amount
        if tx_type == TransactionType.WITHDRAWAL and total > 0:
            total = -total
        quantity = Decimal(1)
        return quantity, None, total

    quantity = received_amount or sent_amount or Decimal(1)
    total = price_amount or quantity
    price = (total / quantity) if quantity else None
    return quantity, price, total


def history_item_to_trade_record(item: dict) -> TradeRecord | None:
    bitvavo_type = (item.get("type") or "").lower()
    if not bitvavo_type:
        return None

    tx_type = map_bitvavo_history_type(bitvavo_type)
    symbol, asset_type = _primary_symbol(item, tx_type)
    quantity, price_eur, total_eur = _quantity_and_price(item, tx_type)

    if total_eur == 0 and tx_type not in (TransactionType.OTHER,):
        return None

    occurred_at = parse_executed_at(item.get("executedAt"))
    external_id = item.get("transactionId") or ""

    return TradeRecord(
        external_id=external_id,
        symbol=symbol,
        side=bitvavo_type,
        quantity=quantity,
        price_eur=price_eur or Decimal(0),
        fee_eur=_parse_decimal(item.get("feesAmount")),
        occurred_at=occurred_at,
        market="",
        asset_type=asset_type,
        transaction_type=tx_type,
        total_eur=total_eur,
    )
