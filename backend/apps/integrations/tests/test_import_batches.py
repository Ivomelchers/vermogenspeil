from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from unittest.mock import patch

from apps.integrations.degiro.import_service import import_degiro_csv_for_user
from apps.integrations.models import PlatformConnection, PlatformImportBatch, PlatformType
from apps.integrations.services.import_batches import purge_connection_data, purge_import_batch
from apps.integrations.testing.fixtures import load_text_fixture
from apps.portfolio.models import Transaction
from apps.portfolio.services import get_or_create_default_portfolio
from apps.portfolio.services.transactions_list import list_portfolio_transactions

User = get_user_model()


class ImportBatchLinkingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="batch@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def test_csv_import_creates_batch_and_links_transactions(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        result = import_degiro_csv_for_user(
            self.user,
            content,
            source_filename="sample-transactions.csv",
        )

        batch = PlatformImportBatch.objects.get(pk=result["import_batch_id"])
        self.assertEqual(batch.transactions_imported, 3)
        self.assertEqual(batch.source_filename, "sample-transactions.csv")
        self.assertEqual(
            Transaction.objects.filter(import_batch=batch).count(),
            3,
        )

    def test_second_import_creates_separate_batch(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        first = import_degiro_csv_for_user(self.user, content, source_filename="first.csv")
        second = import_degiro_csv_for_user(self.user, content, source_filename="second.csv")

        self.assertNotEqual(first["import_batch_id"], second["import_batch_id"])
        self.assertEqual(PlatformImportBatch.objects.filter(user=self.user).count(), 2)
        self.assertEqual(Transaction.objects.filter(portfolio__user=self.user).count(), 3)

    def test_purge_import_batch_removes_linked_transactions_only(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        all_types = load_text_fixture("degiro", "all-transaction-types.csv")
        sample = import_degiro_csv_for_user(self.user, content)
        all_types_result = import_degiro_csv_for_user(self.user, all_types)

        sample_count = Transaction.objects.filter(import_batch_id=sample["import_batch_id"]).count()
        all_types_count = Transaction.objects.filter(
            import_batch_id=all_types_result["import_batch_id"]
        ).count()
        total_before = Transaction.objects.filter(portfolio__user=self.user).count()
        self.assertEqual(sample_count, 3)
        self.assertGreater(all_types_count, 0)
        self.assertEqual(total_before, sample_count + all_types_count)

        result = purge_import_batch(self.user, sample["import_batch_id"])
        self.assertEqual(result["transactions_deleted"], 3)
        self.assertEqual(
            Transaction.objects.filter(portfolio__user=self.user).count(),
            total_before - 3,
        )
        self.assertFalse(
            PlatformImportBatch.objects.filter(pk=sample["import_batch_id"]).exists()
        )

    def test_purge_connection_data_removes_platform_transactions(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        result = import_degiro_csv_for_user(self.user, content)
        connection_id = result["connection_id"]

        purge_result = purge_connection_data(self.user, connection_id)
        self.assertEqual(purge_result["transactions_deleted"], 3)
        self.assertEqual(Transaction.objects.filter(portfolio__user=self.user).count(), 0)
        self.assertTrue(
            PlatformConnection.objects.filter(pk=connection_id).exists()
        )

    def test_filter_transactions_by_import_batch(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        all_types = load_text_fixture("degiro", "all-transaction-types.csv")
        sample = import_degiro_csv_for_user(self.user, content)
        import_degiro_csv_for_user(self.user, all_types)

        portfolio = get_or_create_default_portfolio(self.user)
        filtered = list_portfolio_transactions(
            portfolio,
            import_batch_id=sample["import_batch_id"],
        )
        self.assertEqual(filtered["total"], 3)


class ImportBatchAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="batch-api@example.com",
            password="SecurePass123!",
            first_name="Jan",
            auth_0_id="auth0|batch-api",
            email_verified=True,
        )

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_disconnect_keeps_transactions(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        content = load_text_fixture("degiro", "sample-transactions.csv")
        import_result = import_degiro_csv_for_user(self.user, content)
        connection_id = import_result["connection_id"]

        response = self.client.delete(f"/api/v1/integrations/connections/{connection_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Transaction.objects.filter(portfolio__user=self.user).count(), 3)

        list_response = self.client.get("/api/v1/integrations/connections/")
        self.assertEqual(list_response.data["data"], [])

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_list_and_purge_import_batches_via_api(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        import_result = import_degiro_csv_for_user(
            self.user,
            load_text_fixture("degiro", "sample-transactions.csv"),
            source_filename="sample.csv",
        )
        connection_id = import_result["connection_id"]
        batch_id = import_result["import_batch_id"]

        list_response = self.client.get(
            f"/api/v1/integrations/connections/{connection_id}/import-batches/"
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data["data"]), 1)
        self.assertEqual(list_response.data["data"][0]["id"], batch_id)

        purge_response = self.client.post(
            f"/api/v1/integrations/import-batches/{batch_id}/purge/"
        )
        self.assertEqual(purge_response.status_code, status.HTTP_200_OK)
        self.assertEqual(Transaction.objects.filter(portfolio__user=self.user).count(), 0)
