"""Bitvavo-client die JSON-fixtures leest i.p.v. live API (development/tests)."""

from apps.integrations.bitvavo.client import BitvavoClient
from apps.integrations.testing.fixtures import load_json_fixture


class BitvavoFixtureClient(BitvavoClient):
    """Geen netwerk — responses uit backend/fixtures/bitvavo/."""

    def __init__(self):
        super().__init__(api_key="fixture", api_secret="fixture")

    def get_balance(self) -> list[dict]:
        return load_json_fixture("bitvavo", "balance.json")

    def get_account_history(
        self,
        *,
        from_date_ms: int | None = None,
        to_date_ms: int | None = None,
        max_items: int = 100,
    ) -> list[dict]:
        payload = load_json_fixture("bitvavo", "history-all-types.json")
        items = payload.get("items") or []
        if from_date_ms is None:
            return list(items)
        from apps.integrations.bitvavo.history import parse_executed_at

        return [
            item
            for item in items
            if int(parse_executed_at(item.get("executedAt")).timestamp() * 1000) >= from_date_ms
        ]

    def get_trades(self, market: str, *, limit: int = 500) -> list[dict]:
        filename = f"trades-{market.lower()}.json"
        try:
            return load_json_fixture("bitvavo", filename)
        except FileNotFoundError:
            return []

    def get_markets(self) -> list[dict]:
        return []
