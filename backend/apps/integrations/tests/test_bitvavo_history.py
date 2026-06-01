from django.test import TestCase

from apps.integrations.bitvavo.history import (
    history_item_to_trade_record,
    map_bitvavo_history_type,
)
from apps.integrations.testing.fixtures import load_json_fixture
from apps.portfolio.models import TransactionType


class BitvavoHistoryMappingTests(TestCase):
    def test_maps_all_fixture_types(self):
        payload = load_json_fixture("bitvavo", "history-all-types.json")
        types = set()
        for item in payload["items"]:
            record = history_item_to_trade_record(item)
            self.assertIsNotNone(record, msg=f"missing record for {item.get('type')}")
            types.add(record.transaction_type)

        self.assertEqual(
            types,
            {
                TransactionType.BUY,
                TransactionType.SELL,
                TransactionType.DEPOSIT,
                TransactionType.WITHDRAWAL,
                TransactionType.OTHER,
            },
        )

    def test_map_bitvavo_types(self):
        self.assertEqual(map_bitvavo_history_type("buy"), TransactionType.BUY)
        self.assertEqual(map_bitvavo_history_type("deposit"), TransactionType.DEPOSIT)
        self.assertEqual(map_bitvavo_history_type("staking"), TransactionType.OTHER)
