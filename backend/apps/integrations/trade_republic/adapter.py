from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from apps.accounts.utils.encryption import decrypt_value
from apps.integrations.base import BalanceHolding, PlatformAdapter, PlatformAdapterError, TradeRecord
from apps.integrations.models import PlatformType
from apps.integrations.trade_republic.client import TradeRepublicAPIError, TradeRepublicClient
from apps.portfolio.models import AssetType

# Trade Republic activity type mapping to internal side + transaction_type
_TYPE_MAP = {
    "buy": ("buy", "buy"),
    "savingsplan": ("buy", "buy"),
    "sell": ("sell", "sell"),
    "dividend": ("buy", "dividend"),
}


def _activity_to_trade_record(item: dict) -> TradeRecord | None:
    """Converteer een Trade Republic activity-dict naar een TradeRecord."""
    external_id = str(item.get("id") or "")
    if not external_id:
        return None

    isin = (item.get("isin") or "").strip()
    if not isin:
        return None

    activity_type = (item.get("type") or "").lower()
    mapping = _TYPE_MAP.get(activity_type)
    if mapping is None:
        # Onbekend type — sla over
        return None
    side, transaction_type = mapping

    quantity = Decimal(str(item.get("quantity") or "0"))
    price_eur = Decimal(str(item.get("price") or "0"))
    fee_eur = Decimal(str(item.get("fee") or "0"))

    timestamp = item.get("timestamp") or ""
    try:
        occurred_at = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None

    total_eur = quantity * price_eur if quantity and price_eur else None

    return TradeRecord(
        external_id=external_id,
        symbol=isin,
        side=side,
        quantity=quantity,
        price_eur=price_eur,
        fee_eur=fee_eur,
        occurred_at=occurred_at,
        market="trade_republic",
        asset_type=AssetType.STOCK,
        transaction_type=transaction_type,
        total_eur=total_eur,
    )


class TradeRepublicAdapter(PlatformAdapter):
    platform = PlatformType.TRADE_REPUBLIC

    def _client(self) -> TradeRepublicClient:
        try:
            api_key = decrypt_value(self.connection.api_key_encrypted)
        except Exception as exc:
            raise PlatformAdapterError("API-gegevens konden niet worden ontsleuteld.") from exc

        if not api_key:
            raise PlatformAdapterError("Trade Republic API-key ontbreekt.")

        return TradeRepublicClient(api_key)

    def validate_connection(self) -> bool:
        try:
            self._client().fetch_holdings()
            return True
        except TradeRepublicAPIError as exc:
            raise PlatformAdapterError(str(exc)) from exc

    def fetch_balances(self) -> list[BalanceHolding]:
        client = self._client()
        holdings: list[BalanceHolding] = []

        raw = client.fetch_holdings()
        for entry in raw.get("holdings") or []:
            parsed = client.parse_holding(entry)
            if not parsed:
                continue
            isin, name, quantity = parsed
            holdings.append(
                BalanceHolding(
                    symbol=isin,
                    quantity=quantity,
                    name=name,
                    asset_type=AssetType.STOCK,
                )
            )

        return holdings

    def fetch_transactions(self, since: datetime | None = None) -> list[TradeRecord]:
        client = self._client()
        records: list[TradeRecord] = []

        raw = client.fetch_activities()
        for item in raw.get("items") or []:
            record = _activity_to_trade_record(item)
            if not record:
                continue
            if since and record.occurred_at < since.replace(tzinfo=dt_timezone.utc):
                continue
            records.append(record)

        return records
