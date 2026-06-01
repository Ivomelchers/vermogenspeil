from django.test import TestCase

from apps.integrations.degiro.classification import classify_degiro_description
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
