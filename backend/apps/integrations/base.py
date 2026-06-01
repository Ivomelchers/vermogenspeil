from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class BalanceHolding:
    symbol: str
    quantity: Decimal
    name: str = ""
    asset_type: str = ""


@dataclass
class TradeRecord:
    external_id: str
    symbol: str
    side: str
    quantity: Decimal
    price_eur: Decimal
    fee_eur: Decimal
    occurred_at: datetime
    market: str = ""
    asset_type: str = ""
    transaction_type: str = ""
    total_eur: Decimal | None = None


class PlatformAdapterError(Exception):
    pass


class PlatformAdapter(ABC):
    platform: str

    def __init__(self, connection):
        self.connection = connection

    @abstractmethod
    def validate_connection(self) -> bool:
        """Controleer of credentials geldig zijn."""

    @abstractmethod
    def fetch_balances(self) -> list[BalanceHolding]:
        """Haal huidige balances op."""

    @abstractmethod
    def fetch_transactions(self, since: datetime | None = None) -> list[TradeRecord]:
        """Haal transacties/trades op."""

    def sync(self) -> tuple[int, int]:
        """Synchroniseer balances en transacties naar de database."""
        from apps.integrations.services.sync import apply_sync_results

        if not self.validate_connection():
            raise PlatformAdapterError("Verbinding met platform mislukt.")

        balances = self.fetch_balances()
        trades = self.fetch_transactions()
        return apply_sync_results(self.connection, balances, trades)
