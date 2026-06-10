from datetime import datetime, timezone as dt_timezone

from apps.accounts.utils.encryption import decrypt_value
from apps.integrations.base import BalanceHolding, PlatformAdapter, PlatformAdapterError, TradeRecord
from apps.integrations.bybit.client import BybitAPIError, BybitClient
from apps.integrations.bybit.history import CASH_SYMBOLS, execution_to_trade_record
from apps.integrations.models import PlatformType
from apps.portfolio.models import AssetType


class BybitPlatformAdapter(PlatformAdapter):
    platform = PlatformType.BYBIT

    def _client(self) -> BybitClient:
        try:
            api_key = decrypt_value(self.connection.api_key_encrypted)
            api_secret = decrypt_value(self.connection.api_secret_encrypted)
        except Exception as exc:
            raise PlatformAdapterError("API-gegevens konden niet worden ontsleuteld.") from exc

        if not api_key or not api_secret:
            raise PlatformAdapterError("Bybit API-key of secret ontbreekt.")

        return BybitClient(api_key, api_secret)

    def validate_connection(self) -> bool:
        try:
            self._client().get_wallet_balance()
            return True
        except BybitAPIError as exc:
            raise PlatformAdapterError(str(exc)) from exc

    def fetch_balances(self) -> list[BalanceHolding]:
        client = self._client()
        holdings: list[BalanceHolding] = []

        for entry in client.get_wallet_balance():
            parsed = client.parse_balance(entry)
            if not parsed:
                continue
            symbol, quantity = parsed
            holdings.append(
                BalanceHolding(
                    symbol=symbol,
                    quantity=quantity,
                    name=symbol,
                    asset_type=AssetType.CASH if symbol in CASH_SYMBOLS else AssetType.CRYPTO,
                )
            )

        return holdings

    def fetch_transactions(self, since: datetime | None = None) -> list[TradeRecord]:
        client = self._client()
        records: list[TradeRecord] = []
        since_ms = int(since.timestamp() * 1000) if since else None

        for item in client.get_spot_executions(since_ms=since_ms):
            record = execution_to_trade_record(item)
            if not record:
                continue
            if since and record.occurred_at < since.replace(tzinfo=dt_timezone.utc):
                continue
            records.append(record)

        return records
