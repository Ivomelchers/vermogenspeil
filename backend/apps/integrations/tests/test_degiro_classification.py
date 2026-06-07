from django.test import TestCase
from decimal import Decimal

from apps.integrations.degiro.classification import (
    classify_degiro_description,
    classify_degiro_row,
)
from apps.portfolio.models import TransactionType


class DegiroClassificationTests(TestCase):
    def test_all_supported_types_mapped(self):
        cases = [
            ("Koop", TransactionType.BUY),
            ("Verkoop", TransactionType.SELL),
            ("Dividend", TransactionType.DIVIDEND),
            ("Dividendbelasting", TransactionType.FEE),
            ("iDEAL Deposit", TransactionType.DEPOSIT),
            ("Withdrawal", TransactionType.WITHDRAWAL),
            ("Degiro Fee", TransactionType.FEE),
            ("Flatex Interest", TransactionType.OTHER),
            ("Valuta Creditering", TransactionType.OTHER),
            ("Corporate action", TransactionType.OTHER),
        ]
        for description, expected in cases:
            with self.subTest(description=description):
                self.assertEqual(classify_degiro_description(description), expected)

    def test_row_infers_buy_when_description_is_venue_code(self):
        tx_type = classify_degiro_row(
            description="XAMS",
            quantity=Decimal("8"),
            total=Decimal("-710"),
            product="iShares Core MSCI World UCITS ETF",
            isin="IE00B4L5Y983",
        )
        self.assertEqual(tx_type, TransactionType.BUY)

    def test_row_skips_unknown_description_without_product(self):
        tx_type = classify_degiro_row(
            description="Onbekende regel uit toekomstige export",
            quantity=Decimal("1"),
            total=Decimal("10"),
            product="",
            isin="",
        )
        self.assertIsNone(tx_type)
