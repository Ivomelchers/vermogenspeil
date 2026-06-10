from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from apps.accounts.utils.encryption import decrypt_value
from apps.integrations.base import BalanceHolding, PlatformAdapter, PlatformAdapterError, TradeRecord
from apps.integrations.models import PlatformType
from apps.integrations.trading212.client import Trading212APIError, Trading212Client
from apps.portfolio.models import AssetType

# Trading212 order types mapped to internal side + transaction_type
_BUY_TYPES = {"MARKET_BUY", "LIMIT_BUY"}
_SELL_TYPES = {"MARKET_SELL", "LIMIT_SELL"}
_DIVIDEND_TYPES = {"DIVIDEND"}


def _order_to_trade_record(item: dict) -> TradeRecord | None:
    """Converteer een Trading212 order-dict naar een TradeRecord."""
    external_id = str(item.get("id") or "")
    if not external_id:
        return None

    ticker = (item.get("ticker") or "").strip()
    if not ticker:
        return None

    order_type = (item.get("type") or "").upper()
    if order_type in _BUY_TYPES:
        side = "buy"
        transaction_type = "buy"
    elif order_type in _SELL_TYPES:
        side = "sell"
        transaction_type = "sell"
    elif order_type in _DIVIDEND_TYPES:
        side = "buy"
        transaction_type = "dividend"
    else:
        # Onbekend type — sla over
        return None

    quantity = Decimal(str(item.get("filledQuantity") or "0"))
    price_eur = Decimal(str(item.get("fillPrice") or "0"))
    fee_eur = Decimal(str(item.get("taxes") or item.get("fee") or "0"))

    date_str = item.get("dateExecuted") or ""
    try:
        occurred_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None

    total_eur = quantity * price_eur if quantity and price_eur else None

    return TradeRecord(
        external_id=external_id,
        symbol=ticker,
        side=side,
        quantity=quantity,
        price_eur=price_eur,
        fee_eur=fee_eur,
        occurred_at=occurred_at,
        market="trading212",
        asset_type=AssetType.STOCK,
        transaction_type=transaction_type,
        total_eur=total_eur,
    )


class Trading212Adapter(PlatformAdapter):
    platform = PlatformType.TRADING212

    def _client(self) -> Trading212Client:
        try:
            api_key = decrypt_value(self.connection.api_key_encrypted)
        except Exception as exc:
            raise PlatformAdapterError("API-gegevens konden niet worden ontsleuteld.") from exc

        if not api_key:
            raise PlatformAdapterError("Trading212 API-key ontbreekt.")

        sandbox = getattr(self.connection, "is_demo", False)
        return Trading212Client(api_key, sandbox=sandbox)

    def validate_connection(self) -> bool:
        try:
            self._client().fetch_account_cash()
            return True
        except Trading212APIError as exc:
            raise PlatformAdapterError(str(exc)) from exc

    def fetch_balances(self) -> list[BalanceHolding]:
        client = self._client()
        holdings: list[BalanceHolding] = []

        for entry in client.fetch_portfolio():
            parsed = client.parse_position(entry)
            if not parsed:
                continue
            ticker, quantity = parsed
            holdings.append(
                BalanceHolding(
                    symbol=ticker,
                    quantity=quantity,
                    name=ticker,
                    asset_type=AssetType.STOCK,
                )
            )

        # Voeg cash-saldo toe als aparte holding
        try:
            cash_data = client.fetch_account_cash()
            free_cash = Decimal(str(cash_data.get("free") or "0"))
            if free_cash > 0:
                holdings.append(
                    BalanceHolding(
                        symbol="EUR",
                        quantity=free_cash,
                        name="Cash",
                        asset_type=AssetType.CASH,
                    )
                )
        except Trading212APIError:
            pass  # Cash-saldo is optioneel; positie-data is al verwerkt

        return holdings

    def fetch_transactions(self, since: datetime | None = None) -> list[TradeRecord]:
        client = self._client()
        records: list[TradeRecord] = []

        for item in client.fetch_order_history():
            record = _order_to_trade_record(item)
            if not record:
                continue
            if since and record.occurred_at < since.replace(tzinfo=dt_timezone.utc):
                continue
            records.append(record)

        return records
