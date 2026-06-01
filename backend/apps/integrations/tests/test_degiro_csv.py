from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.integrations.degiro.import_service import import_degiro_csv_for_user
from apps.integrations.degiro.parser import parse_degiro_csv
from apps.portfolio.models import Position, Transaction

User = get_user_model()

FIXTURE = (
    Path(__file__).resolve().parents[3] / "fixtures" / "degiro" / "sample-transactions.csv"
)


class DegiroParserTests(TestCase):
    def test_parse_sample_fixture(self):
        content = FIXTURE.read_text(encoding="utf-8-sig")
        rows = parse_degiro_csv(content)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].side, "buy")


class DegiroImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="degiro@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def test_import_creates_transactions_and_positions(self):
        content = FIXTURE.read_text(encoding="utf-8-sig")
        result = import_degiro_csv_for_user(self.user, content)

        self.assertEqual(result["transactions_imported"], 3)
        self.assertEqual(Transaction.objects.filter(portfolio__user=self.user).count(), 3)
        self.assertGreater(Position.objects.filter(portfolio__user=self.user).count(), 0)

    def test_duplicate_import_skips_rows(self):
        content = FIXTURE.read_text(encoding="utf-8-sig")
        import_degiro_csv_for_user(self.user, content)
        second = import_degiro_csv_for_user(self.user, content)

        self.assertEqual(second["transactions_imported"], 0)
        self.assertEqual(second["transactions_skipped"], 3)
