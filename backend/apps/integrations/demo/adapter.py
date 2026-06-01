from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from apps.integrations.base import BalanceHolding, PlatformAdapter, TradeRecord
from apps.integrations.models import PlatformType
from apps.portfolio.models import AssetType

_UTC = dt_timezone.utc

# Vaste datums zodat herhaalde demo-sync geen dubbele transacties aanmaakt.
_DEMO_DATES = {
    "demo-btc-1": datetime(2026, 2, 1, 12, 0, tzinfo=_UTC),
    "demo-btc-2": datetime(2026, 4, 17, 12, 0, tzinfo=_UTC),
    "demo-eth-1": datetime(2026, 5, 2, 12, 0, tzinfo=_UTC),
    "demo-iwda-1": datetime(2025, 11, 13, 12, 0, tzinfo=_UTC),
    "demo-iwda-2": datetime(2026, 4, 2, 12, 0, tzinfo=_UTC),
    "demo-asml-1": datetime(2026, 3, 3, 12, 0, tzinfo=_UTC),
}


def _demo_occurred_at(external_id: str) -> datetime:
    return _DEMO_DATES.get(external_id, datetime(2026, 1, 1, 12, 0, tzinfo=_UTC))


class DemoPlatformAdapter(PlatformAdapter):
    """Vaste voorbeelddata — geen externe API. Alleen voor is_demo-koppelingen."""

    def validate_connection(self) -> bool:
        return True

    def fetch_balances(self) -> list[BalanceHolding]:
        if self.connection.platform == PlatformType.BITVAVO:
            return [
                BalanceHolding(
                    symbol="BTC",
                    quantity=Decimal("0.42"),
                    name="Bitcoin",
                    asset_type=AssetType.CRYPTO,
                ),
                BalanceHolding(
                    symbol="ETH",
                    quantity=Decimal("1.15"),
                    name="Ethereum",
                    asset_type=AssetType.CRYPTO,
                ),
            ]
        if self.connection.platform == PlatformType.DEGIRO:
            return [
                BalanceHolding(
                    symbol="IWDA",
                    quantity=Decimal("12"),
                    name="iShares MSCI World",
                    asset_type=AssetType.ETF,
                ),
                BalanceHolding(
                    symbol="ASML",
                    quantity=Decimal("5"),
                    name="ASML Holding",
                    asset_type=AssetType.STOCK,
                ),
            ]
        return [
            BalanceHolding(symbol="BTC", quantity=Decimal("0.1"), name="Bitcoin"),
        ]

    def fetch_transactions(self, since: datetime | None = None) -> list[TradeRecord]:
        if self.connection.platform == PlatformType.BITVAVO:
            return [
                TradeRecord(
                    external_id="demo-btc-1",
                    symbol="BTC",
                    side="buy",
                    quantity=Decimal("0.15"),
                    price_eur=Decimal("52000"),
                    fee_eur=Decimal("0.25"),
                    occurred_at=_demo_occurred_at("demo-btc-1"),
                    asset_type=AssetType.CRYPTO,
                ),
                TradeRecord(
                    external_id="demo-btc-2",
                    symbol="BTC",
                    side="buy",
                    quantity=Decimal("0.27"),
                    price_eur=Decimal("61000"),
                    fee_eur=Decimal("0.30"),
                    occurred_at=_utc_days_ago(45),
                    asset_type=AssetType.CRYPTO,
                ),
                TradeRecord(
                    external_id="demo-eth-1",
                    symbol="ETH",
                    side="buy",
                    quantity=Decimal("1.15"),
                    price_eur=Decimal("2800"),
                    fee_eur=Decimal("0.18"),
                    occurred_at=_demo_occurred_at("demo-eth-1"),
                    asset_type=AssetType.CRYPTO,
                ),
            ]
        if self.connection.platform == PlatformType.DEGIRO:
            return [
                TradeRecord(
                    external_id="demo-iwda-1",
                    symbol="IWDA",
                    side="buy",
                    quantity=Decimal("8"),
                    price_eur=Decimal("88.50"),
                    fee_eur=Decimal("0"),
                    occurred_at=_demo_occurred_at("demo-iwda-1"),
                    asset_type=AssetType.ETF,
                ),
                TradeRecord(
                    external_id="demo-iwda-2",
                    symbol="IWDA",
                    side="buy",
                    quantity=Decimal("4"),
                    price_eur=Decimal("92.10"),
                    fee_eur=Decimal("0"),
                    occurred_at=_demo_occurred_at("demo-iwda-2"),
                    asset_type=AssetType.ETF,
                ),
                TradeRecord(
                    external_id="demo-asml-1",
                    symbol="ASML",
                    side="buy",
                    quantity=Decimal("5"),
                    price_eur=Decimal("680"),
                    fee_eur=Decimal("2.50"),
                    occurred_at=_demo_occurred_at("demo-asml-1"),
                    asset_type=AssetType.STOCK,
                ),
            ]
        return []
