from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.integrations.degiro.import_service import import_degiro_csv_for_user
from apps.integrations.models import ConnectionMethod, PlatformConnection, PlatformType, SyncJob, SyncStatus
from apps.integrations.services.sync import run_connection_sync
from apps.integrations.testing.fixtures import load_text_fixture

User = get_user_model()


class DegiroCsvSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="degiro-sync@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )
        content = load_text_fixture("degiro", "sample-transactions.csv")
        import_degiro_csv_for_user(self.user, content)

    def test_csv_connection_sync_succeeds_without_api_adapter(self):
        connection = PlatformConnection.objects.get(
            user=self.user,
            platform=PlatformType.DEGIRO,
            connection_method=ConnectionMethod.CSV,
        )
        connection.status = SyncStatus.ERROR
        connection.last_error = "Platform degiro wordt nog niet ondersteund."
        connection.save()

        sync_job = SyncJob.objects.create(connection=connection, status=SyncStatus.PENDING)
        run_connection_sync(sync_job.id)

        connection.refresh_from_db()
        sync_job.refresh_from_db()

        self.assertEqual(sync_job.status, SyncStatus.SUCCESS)
        self.assertEqual(connection.status, SyncStatus.SUCCESS)
        self.assertEqual(connection.last_error, "")
