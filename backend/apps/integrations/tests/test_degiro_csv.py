from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from unittest.mock import patch

from apps.integrations.degiro.import_service import import_degiro_csv_for_user
from apps.integrations.degiro.parser import parse_degiro_csv
from apps.integrations.testing.fixtures import load_bytes_fixture, load_text_fixture
from apps.portfolio.models import AssetType, Position, Transaction, TransactionType

User = get_user_model()


class DegiroParserTests(TestCase):
    def test_parse_sample_fixture_buy_only(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        result = parse_degiro_csv(content)
        self.assertEqual(len(result.rows), 3)
        self.assertTrue(
            all(r.transaction_type == TransactionType.BUY for r in result.rows),
        )

    def test_parse_all_transaction_types_fixture(self):
        content = load_text_fixture("degiro", "all-transaction-types.csv")
        result = parse_degiro_csv(content)
        rows = result.rows
        types = {r.transaction_type for r in rows}
        self.assertEqual(len(rows), 9)
        self.assertEqual(
            types,
            {
                TransactionType.BUY,
                TransactionType.SELL,
                TransactionType.DIVIDEND,
                TransactionType.FEE,
                TransactionType.DEPOSIT,
                TransactionType.WITHDRAWAL,
                TransactionType.OTHER,
            },
        )


class DegiroImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="degiro@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def test_import_creates_transactions_and_positions(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        result = import_degiro_csv_for_user(self.user, content)

        self.assertEqual(result["transactions_imported"], 3)
        self.assertEqual(Transaction.objects.filter(portfolio__user=self.user).count(), 3)
        self.assertGreater(Position.objects.filter(portfolio__user=self.user).count(), 0)

    def test_import_all_types_includes_cash_position(self):
        content = load_text_fixture("degiro", "all-transaction-types.csv")
        result = import_degiro_csv_for_user(self.user, content)

        self.assertEqual(result["transactions_imported"], 9)
        self.assertIn(TransactionType.DEPOSIT, result["by_type"])
        self.assertIn(TransactionType.DIVIDEND, result["by_type"])

        cash_positions = Position.objects.filter(
            portfolio__user=self.user,
            asset__asset_type=AssetType.CASH,
        )
        self.assertTrue(cash_positions.exists())
        self.assertGreater(cash_positions.first().quantity, 0)

    def test_duplicate_import_skips_rows(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        import_degiro_csv_for_user(self.user, content)
        second = import_degiro_csv_for_user(self.user, content)

        self.assertEqual(second["transactions_imported"], 0)
        self.assertEqual(second["transactions_skipped"], 3)


class DegiroCsvUploadAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="degiro-api@example.com",
            password="SecurePass123!",
            first_name="Jan",
            auth_0_id="auth0|degiro-api",
            email_verified=True,
        )

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_multipart_csv_upload_accepted(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        content = load_bytes_fixture("degiro", "sample-transactions.csv")
        upload = SimpleUploadedFile(
            "transactions.csv",
            content,
            content_type="text/csv",
        )

        response = self.client.post(
            "/api/v1/integrations/connections/degiro/import/",
            {"file": upload},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["transactions_imported"], 3)
        self.assertIn("trust_summary", response.data["data"])
