from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from apps.accounts.utils.encryption import decrypt_value
from apps.integrations.base import BalanceHolding, PlatformAdapter, PlatformAdapterError, TradeRecord
from apps.integrations.models import PlatformType
from apps.integrations.saxo.client import SaxoAPIError, SaxoClient
from apps.portfolio.models import AssetType


class SaxoPlatformAdapter(PlatformAdapter):
    """Saxo Bank API adapter."""

    platform = PlatformType.SAXO

    def _client(self) -> SaxoClient:
        """Get Saxo API client from encrypted credentials (either OAuth token or API key)."""
        try:
            api_key_decrypted = decrypt_value(self.connection.api_key_encrypted)
            api_secret_decrypted = decrypt_value(self.connection.api_secret_encrypted) if self.connection.api_secret_encrypted else None
        except Exception as exc:
            raise PlatformAdapterError("Saxo-gegevens konden niet worden ontsleuteld.") from exc

        if not api_key_decrypted:
            raise PlatformAdapterError("Saxo-gegevens ontbreken.")

        # Determine if this is API key or OAuth token
        # OAuth: api_key_encrypted = access_token, api_secret_encrypted = refresh_token
        # API Key: api_key_encrypted = api_key, api_secret_encrypted = empty/optional

        if api_secret_decrypted:
            # Likely OAuth (has refresh token)
            return SaxoClient(access_token=api_key_decrypted, refresh_token=api_secret_decrypted)
        else:
            # Likely API key (no refresh token)
            return SaxoClient(api_key=api_key_decrypted)

    def validate_connection(self) -> bool:
        """Verify connection by fetching client info."""
        try:
            client = self._client()
            client.get_client_me()
            return True
        except SaxoAPIError as exc:
            raise PlatformAdapterError(f"Saxo-verbinding mislukt: {exc}") from exc

    def fetch_balances(self) -> list[BalanceHolding]:
        """Fetch current holdings from Saxo."""
        client = self._client()
        holdings: list[BalanceHolding] = []

        try:
            # Get client info to find accounts
            client_info = client.get_client_me()
            client_key = client_info.get("ClientKey")

            if not client_key:
                raise PlatformAdapterError("ClientKey niet gevonden.")

            # Get accounts
            accounts = client.get_accounts(client_key)

            for account in accounts:
                account_key = account.get("AccountKey")
                if not account_key:
                    continue

                # Get positions for this account
                try:
                    positions = client.get_positions(account_key=account_key)
                    for pos in positions:
                        symbol = pos.get("Uic") or pos.get("Identifier", "")
                        if not symbol:
                            continue

                        quantity = Decimal(str(pos.get("NetPosition", 0)))
                        if quantity == 0:
                            continue

                        name = pos.get("DisplayAndFormat", {}).get("Description", symbol)
                        asset_type = self._infer_asset_type(pos)

                        holdings.append(
                            BalanceHolding(
                                symbol=str(symbol),
                                quantity=quantity,
                                name=name,
                                asset_type=asset_type,
                            )
                        )
                except SaxoAPIError:
                    # Skip account if positions fail
                    continue

            return holdings

        except SaxoAPIError as exc:
            raise PlatformAdapterError(f"Fout bij ophalen posities: {exc}") from exc

    def fetch_transactions(self, since: datetime | None = None) -> list[TradeRecord]:
        """Fetch transaction history from Saxo."""
        client = self._client()
        records: list[TradeRecord] = []

        try:
            # Get client info
            client_info = client.get_client_me()
            client_key = client_info.get("ClientKey")

            if not client_key:
                raise PlatformAdapterError("ClientKey niet gevonden.")

            # Get all transactions for this client
            try:
                transactions = client.get_account_history(client_key=client_key)
                for tx in transactions:
                    record = self._transaction_to_record(tx)
                    if record and (not since or record.occurred_at >= since):
                        records.append(record)
            except SaxoAPIError:
                # Fallback: try getting trades per account
                accounts = client.get_accounts(client_key)
                for account in accounts:
                    account_key = account.get("AccountKey")
                    if not account_key:
                        continue

                    try:
                        trades = client.get_trades(client_key=client_key, count=1000)
                        for trade in trades:
                            record = self._trade_to_record(trade, account_key)
                            if record and (not since or record.occurred_at >= since):
                                records.append(record)
                    except SaxoAPIError:
                        continue

            return records

        except SaxoAPIError as exc:
            raise PlatformAdapterError(f"Fout bij ophalen transacties: {exc}") from exc

    def _infer_asset_type(self, position: dict) -> str:
        """Infer asset type from position data."""
        asset_type_raw = position.get("AssetType", "").lower()

        if "stock" in asset_type_raw:
            return AssetType.STOCK
        elif "etf" in asset_type_raw or "fund" in asset_type_raw:
            return AssetType.ETF
        elif "option" in asset_type_raw:
            return AssetType.STOCK  # Treat options as stock for now
        elif "future" in asset_type_raw:
            return AssetType.STOCK  # Treat futures as stock
        else:
            return AssetType.STOCK

    def _transaction_to_record(self, tx: dict) -> TradeRecord | None:
        """Convert Saxo transaction to TradeRecord."""
        try:
            tx_id = tx.get("Id", "")
            if not tx_id:
                return None

            symbol = tx.get("Uic", "") or tx.get("Identifier", "")
            if not symbol:
                return None

            # Get transaction type
            tx_type_raw = tx.get("TransactionType", "")
            side = "BUY" if "BUY" in tx_type_raw.upper() else "SELL"

            # Amount/quantity
            quantity = Decimal(str(tx.get("Amount", 0)))
            if quantity == 0:
                return None

            price_eur = Decimal(str(tx.get("Price", 0)))
            fee_eur = Decimal(str(tx.get("Charges", 0)))  # or "Cost"
            total_eur = Decimal(str(tx.get("Value", 0)))

            # Parse executed time
            executed_at = tx.get("ExecutionTime", "") or tx.get("TransactionTime", "")
            if executed_at:
                try:
                    occurred_at = datetime.fromisoformat(executed_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    occurred_at = datetime.utcnow()
            else:
                occurred_at = datetime.utcnow()

            return TradeRecord(
                external_id=str(tx_id),
                symbol=str(symbol),
                side=side,
                quantity=quantity,
                price_eur=price_eur,
                fee_eur=fee_eur,
                occurred_at=occurred_at,
                asset_type=self._infer_asset_type(tx),
                transaction_type=self._normalize_transaction_type_from_tx(tx_type_raw),
                total_eur=total_eur,
            )
        except Exception:
            return None

    def _normalize_transaction_type_from_tx(self, tx_type: str) -> str:
        """Normalize Saxo transaction type string."""
        from apps.portfolio.models import TransactionType

        raw = (tx_type or "").upper()

        if "BUY" in raw:
            return TransactionType.BUY
        elif "SELL" in raw:
            return TransactionType.SELL
        elif "DIVIDEND" in raw or "DISTRIBUTION" in raw:
            return TransactionType.DIVIDEND
        elif "DEPOSIT" in raw or "TRANSFER IN" in raw:
            return TransactionType.DEPOSIT
        elif "WITHDRAWAL" in raw or "TRANSFER OUT" in raw:
            return TransactionType.WITHDRAWAL
        elif "COST" in raw or "FEE" in raw or "CHARGE" in raw:
            return TransactionType.FEE
        else:
            return TransactionType.UNKNOWN

    def _trade_to_record(self, trade: dict, account_key: str) -> TradeRecord | None:
        """Convert Saxo trade to TradeRecord."""
        try:
            trade_id = trade.get("TradeId", "")
            if not trade_id:
                return None

            symbol = trade.get("Uic", "") or trade.get("Identifier", "")
            if not symbol:
                return None

            # Determine side (Buy=long, Sell=short)
            side = "BUY" if trade.get("BuySell", "").upper() == "BUY" else "SELL"

            quantity = Decimal(str(trade.get("Amount", 0)))
            if quantity == 0:
                return None

            price_eur = Decimal(str(trade.get("OpenPrice", 0)))
            fee_eur = Decimal(str(trade.get("CostAmount", 0)))

            # Calculate total
            total_eur = quantity * price_eur

            # Parse executed time
            executed_at = trade.get("ExecutionTime", "")
            if executed_at:
                try:
                    occurred_at = datetime.fromisoformat(executed_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    occurred_at = datetime.utcnow()
            else:
                occurred_at = datetime.utcnow()

            return TradeRecord(
                external_id=str(trade_id),
                symbol=str(symbol),
                side=side,
                quantity=quantity,
                price_eur=price_eur,
                fee_eur=fee_eur,
                occurred_at=occurred_at,
                asset_type=self._infer_asset_type(trade),
                transaction_type="TRADE",
                total_eur=total_eur,
            )
        except Exception:
            return None
