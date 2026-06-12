from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from apps.accounts.utils.encryption import decrypt_value
from apps.integrations.base import BalanceHolding, PlatformAdapter, PlatformAdapterError, TradeRecord
from apps.integrations.models import PlatformType
from apps.integrations.saxo.client import SaxoAPIError, SaxoClient
from apps.portfolio.models import AssetType, TransactionType


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
            # OAuth (has refresh token)
            client = SaxoClient(access_token=api_key_decrypted, refresh_token=api_secret_decrypted)
            self._client_instance = client  # Store for token refresh
            return client
        else:
            # API key (no refresh token)
            return SaxoClient(api_key=api_key_decrypted)

    def _refresh_and_retry(self, client: SaxoClient, method: str, endpoint: str, **kwargs) -> dict:
        """Attempt to refresh OAuth tokens and retry the request."""
        # Try to refresh the access token
        result = client.refresh_access_token()
        if not result:
            raise PlatformAdapterError("Token refresh failed")

        new_access_token, new_refresh_token = result

        # Update stored tokens in the connection
        from apps.integrations.services.credentials import store_api_credentials
        store_api_credentials(
            self.connection,
            api_key=new_access_token,
            api_secret=new_refresh_token,
        )
        print(f"✅ [SAXO] Tokens refreshed and updated for connection {self.connection.id}")

        # Retry the request with new client
        return client._request(method, endpoint, **kwargs)

    def validate_connection(self) -> bool:
        """Verify connection by fetching client info. Attempts token refresh on 401."""
        try:
            client = self._client()
            client.get_client_me()
            return True
        except SaxoAPIError as exc:
            # Check if it's a 401 Unauthorized (token expired)
            if "401" in str(exc):
                print(f"🔄 [SAXO] Token expired, attempting refresh...")
                try:
                    # Retry after refresh
                    self._refresh_and_retry(client, "GET", "port/v1/clients/me")
                    print(f"✅ [SAXO] Validation succeeded after token refresh")
                    return True
                except Exception as refresh_exc:
                    raise PlatformAdapterError(f"Saxo-verbinding mislukt (token refresh failed): {refresh_exc}") from refresh_exc

            raise PlatformAdapterError(f"Saxo-verbinding mislukt: {exc}") from exc

    def fetch_balances(self) -> list[BalanceHolding]:
        """Fetch current holdings from Saxo."""
        import logging
        logger = logging.getLogger(__name__)

        client = self._client()
        holdings: list[BalanceHolding] = []

        try:
            # Get client info to find accounts
            client_info = client.get_client_me()
            client_key = client_info.get("ClientKey")
            logger.info(f"[Saxo] Fetching balances - ClientKey: {client_key}")

            if not client_key:
                raise PlatformAdapterError("ClientKey niet gevonden.")

            # Get accounts
            accounts = client.get_accounts(client_key)
            logger.info(f"[Saxo] Found {len(accounts)} accounts")

            # Get positions for all accounts using ClientKey (more efficient)
            try:
                positions = client.get_positions(client_key=client_key)
                logger.info(f"[Saxo] Got {len(positions)} positions from API")

                for pos in positions:
                    # Get Uic from PositionBase
                    pos_base = pos.get("PositionBase", {})
                    symbol = str(pos_base.get("Uic", ""))
                    if not symbol:
                        continue

                    # Get quantity from PositionBase.Amount
                    quantity = Decimal(str(pos_base.get("Amount", 0)))
                    if quantity == 0:
                        continue

                    # Get name from DisplayAndFormat.Description or Symbol
                    display = pos.get("DisplayAndFormat", {})
                    name = display.get("Description", "") or display.get("Symbol", symbol)
                    asset_type = self._infer_asset_type(pos_base)

                    holdings.append(
                        BalanceHolding(
                            symbol=str(symbol),
                            quantity=quantity,
                            name=name,
                            asset_type=asset_type,
                        )
                    )
            except SaxoAPIError as exc:
                # Error fetching positions
                logger.error(f"[Saxo] Error fetching positions: {exc}", exc_info=True)

            logger.info(f"[Saxo] Total holdings returned: {len(holdings)}")
            return holdings

        except SaxoAPIError as exc:
            logger.error(f"[Saxo] Error in fetch_balances: {exc}", exc_info=True)
            raise PlatformAdapterError(f"Fout bij ophalen posities: {exc}") from exc

    def fetch_transactions(self, since: datetime | None = None) -> list[TradeRecord]:
        """Fetch transaction history from Saxo (includes executed trades and pending orders)."""
        import logging
        logger = logging.getLogger(__name__)

        client = self._client()
        records: list[TradeRecord] = []

        try:
            # Get client info
            client_info = client.get_client_me()
            client_key = client_info.get("ClientKey")
            logger.info(f"[Saxo] Fetching transactions - ClientKey: {client_key}, since: {since}")

            if not client_key:
                raise PlatformAdapterError("ClientKey niet gevonden.")

            # Get all transactions for this client
            try:
                transactions = client.get_account_history(client_key=client_key)
                logger.info(f"[Saxo] Got {len(transactions)} transactions from account history API")
                for tx in transactions:
                    record = self._transaction_to_record(tx)
                    if record and (not since or record.occurred_at >= since):
                        records.append(record)
            except SaxoAPIError as exc:
                # Fallback: try getting trades per account
                logger.warning(f"[Saxo] Account history API failed: {exc}, trying trades API")
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

            # Also fetch pending orders (orders that haven't been executed yet)
            try:
                orders = client.get_orders()
                logger.info(f"[Saxo] Got {len(orders)} pending orders")
                for order in orders:
                    record = self._order_to_record(order)
                    if record and (not since or record.occurred_at >= since):
                        records.append(record)
            except SaxoAPIError as exc:
                logger.warning(f"[Saxo] Could not fetch pending orders: {exc}")

            logger.info(f"[Saxo] Total transactions returned: {len(records)}")
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
                    occurred_at = datetime.now(dt_timezone.utc)
            else:
                occurred_at = datetime.now(dt_timezone.utc)

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

            # Get symbol: prefer InstrumentSymbol (from trades API), fallback to DisplayAndFormat, then Uic
            symbol = (
                trade.get("InstrumentSymbol", "") or  # Trades API returns InstrumentSymbol
                trade.get("DisplayAndFormat", {}).get("Symbol", "") or  # Orders API returns DisplayAndFormat.Symbol
                str(trade.get("Uic", ""))  # Fallback to numeric Uic
            )
            if not symbol:
                return None

            # Determine side (Buy=long, Sell=short)
            side = "BUY" if trade.get("BuySell", "").upper() == "BUY" else "SELL"

            quantity = Decimal(str(trade.get("Amount", 0)))
            if quantity == 0:
                return None

            # Trades API uses "Price", not "OpenPrice"
            price_eur = Decimal(str(trade.get("Price", 0) or trade.get("OpenPrice", 0)))
            fee_eur = Decimal(str(trade.get("CostAmount", 0) or 0))

            # Calculate total
            total_eur = quantity * price_eur

            # Parse executed time
            executed_at = trade.get("ExecutionTime", "")
            if executed_at:
                try:
                    occurred_at = datetime.fromisoformat(executed_at.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    occurred_at = datetime.now(dt_timezone.utc)
            else:
                occurred_at = datetime.now(dt_timezone.utc)

            # Determine transaction type based on side (BUY or SELL)
            transaction_type = TransactionType.BUY if side == "BUY" else TransactionType.SELL

            return TradeRecord(
                external_id=str(trade_id),
                symbol=str(symbol),
                side=side,
                quantity=quantity,
                price_eur=price_eur,
                fee_eur=fee_eur,
                occurred_at=occurred_at,
                asset_type=self._infer_asset_type(trade),
                transaction_type=transaction_type,
                total_eur=total_eur,
            )
        except Exception:
            return None

    def _order_to_record(self, order: dict) -> TradeRecord | None:
        """Convert Saxo pending order to TradeRecord (marked as PENDING_ORDER)."""
        try:
            order_id = order.get("OrderId", "")
            if not order_id:
                return None

            # Get symbol from DisplayAndFormat first (e.g., "EURDKK"), fallback to Uic
            display = order.get("DisplayAndFormat", {})
            symbol = display.get("Symbol", "") or str(order.get("Uic", ""))
            if not symbol:
                return None

            # Determine side
            side = "BUY" if order.get("BuySell", "").upper() == "BUY" else "SELL"

            quantity = Decimal(str(order.get("Amount", 0)))
            if quantity == 0:
                return None

            # Use OrderPrice for pending orders, or CurrentPrice if available
            price_eur = Decimal(str(order.get("Price", 0) or order.get("CurrentPrice", 0)))

            # Calculate total
            total_eur = quantity * price_eur

            # Parse order time
            order_time = order.get("OrderTime", "")
            if order_time:
                try:
                    occurred_at = datetime.fromisoformat(order_time.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    occurred_at = datetime.now(dt_timezone.utc)
            else:
                occurred_at = datetime.now(dt_timezone.utc)

            # Determine transaction type based on side (pending orders are BUY/SELL trades)
            transaction_type = TransactionType.BUY if side == "BUY" else TransactionType.SELL

            return TradeRecord(
                external_id=f"ORDER_{order_id}",
                symbol=str(symbol),
                side=side,
                quantity=quantity,
                price_eur=price_eur,
                fee_eur=Decimal(0),
                occurred_at=occurred_at,
                asset_type=self._infer_asset_type(order),
                transaction_type=transaction_type,
                total_eur=total_eur,
            )
        except Exception:
            return None
