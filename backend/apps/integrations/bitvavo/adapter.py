from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from apps.accounts.utils.encryption import decrypt_value
from apps.integrations.base import BalanceHolding, PlatformAdapter, PlatformAdapterError, TradeRecord
from apps.integrations.bitvavo.client import BitvavoAPIError, BitvavoClient
from apps.integrations.models import PlatformType


class BitvavoPlatformAdapter(PlatformAdapter):
    platform = PlatformType.BITVAVO

    def _client(self) -> BitvavoClient:
        try:
            api_key = decrypt_value(self.connection.api_key_encrypted)
            api_secret = decrypt_value(self.connection.api_secret_encrypted)
        except Exception as exc:
            raise PlatformAdapterError("API-gegevens konden niet worden ontsleuteld.") from exc

        if not api_key or not api_secret:
            raise PlatformAdapterError("Bitvavo API-key of secret ontbreekt.")

        return BitvavoClient(api_key, api_secret)

    def validate_connection(self) -> bool:
        try:
            self._client().get_balance()
            return True
        except BitvavoAPIError as exc:
            raise PlatformAdapterError(str(exc)) from exc

    def fetch_balances(self) -> list[BalanceHolding]:
        client = self._client()
        holdings: list[BalanceHolding] = []

        for entry in client.get_balance():
            parsed = client.parse_balance(entry)
            if not parsed:
                continue
            symbol, quantity = parsed
            holdings.append(
                BalanceHolding(
                    symbol=symbol,
                    quantity=quantity,
                    name=symbol,
                )
            )

        return holdings

    def fetch_transactions(self, since: datetime | None = None) -> list[TradeRecord]:
        client = self._client()
        records: list[TradeRecord] = []
        since_ms = int(since.timestamp() * 1000) if since else 0

        balances = client.get_balance()
        markets_with_balance = set()
        for entry in balances:
            symbol = entry.get("symbol", "")
            if symbol and symbol != "EUR":
                markets_with_balance.add(f"{symbol}-EUR")

        for market in sorted(markets_with_balance):
            try:
                trades = client.get_trades(market)
            except BitvavoAPIError:
                continue

            for trade in trades:
                parsed = client.parse_trade(trade, market)
                if parsed["occurred_at_ms"] < since_ms:
                    continue
                occurred_at = datetime.fromtimestamp(
                    parsed["occurred_at_ms"] / 1000,
                    tz=dt_timezone.utc,
                )
                records.append(
                    TradeRecord(
                        external_id=parsed["external_id"],
                        symbol=parsed["symbol"],
                        side=parsed["side"],
                        quantity=parsed["quantity"],
                        price_eur=parsed["price_eur"],
                        fee_eur=parsed["fee_eur"],
                        occurred_at=occurred_at,
                        market=parsed["market"],
                    )
                )

        return records
