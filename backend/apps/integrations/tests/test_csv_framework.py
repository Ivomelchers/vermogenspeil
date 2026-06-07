from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from unittest.mock import patch

from apps.integrations.csv.ai_column_mapping import AiColumnMappingResult

from apps.integrations.csv.base import CsvParseError
from apps.integrations.csv.detection import detect_csv_platform, validate_csv_for_platform
from apps.integrations.csv.import_service import import_csv_for_user
from apps.integrations.csv.preview import FAILURE_UNSUPPORTED, preview_csv_for_user
from apps.integrations.models import PlatformType
from apps.integrations.testing.fixtures import load_bytes_fixture, load_text_fixture
from apps.portfolio.models import Transaction

User = get_user_model()


class CsvDetectionTests(TestCase):
    def test_detect_degiro_fixture(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        matches = detect_csv_platform(content)
        self.assertGreaterEqual(len(matches), 1)
        self.assertEqual(matches[0].platform, PlatformType.DEGIRO)
        self.assertGreaterEqual(matches[0].confidence, 0.85)

    def test_reject_random_csv(self):
        content = "foo,bar\n1,2\n"
        matches = detect_csv_platform(content)
        self.assertEqual(matches, [])

    def test_validate_platform_mismatch(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        # Zelfde bestand is wél DEGIRO — test verkeerd platform via fake header file
        bad = "Symbol,Side,Quantity\nBTC,BUY,1\n"
        with self.assertRaises(CsvParseError):
            validate_csv_for_platform(bad, PlatformType.DEGIRO)


class CsvPreviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="csv-preview@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def test_preview_ok_counts_new_and_duplicate(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        first = preview_csv_for_user(self.user, content, platform=PlatformType.DEGIRO)
        self.assertEqual(first["status"], "ok")
        self.assertEqual(first["summary"]["new"], 3)

        import_csv_for_user(self.user, content, platform=PlatformType.DEGIRO)
        second = preview_csv_for_user(self.user, content, platform=PlatformType.DEGIRO)
        self.assertEqual(second["summary"]["new"], 0)
        self.assertEqual(second["summary"]["duplicate"], 3)
        self.assertFalse(second["can_confirm_import"])

    @patch("apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_drifted_degiro_headers_parse_via_schema_without_ai(self, mock_ai):
        content = load_text_fixture("degiro", "requires-ai-mapping-v1.csv")

        result = preview_csv_for_user(self.user, content, platform=PlatformType.DEGIRO)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"]["new"], 1)
        self.assertFalse(result["column_mapping"]["ai_used"])
        self.assertEqual(result["column_mapping"]["source"], "schema")
        self.assertTrue(result["can_confirm_import"])
        mock_ai.assert_not_called()

    @patch("apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_v2_degiro_headers_parse_via_schema_without_ai(self, mock_ai):
        content = load_text_fixture("degiro", "requires-ai-mapping-v2.csv")

        result = preview_csv_for_user(self.user, content, platform=PlatformType.DEGIRO)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"]["new"], 1)
        self.assertFalse(result["column_mapping"]["ai_used"])
        self.assertTrue(result["can_confirm_import"])
        mock_ai.assert_not_called()

    @patch("apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_preview_allows_confirm_when_ai_resolved_columns(self, mock_ai):
        content = (
            "Tx date;Tx time;Asset title;ID code;Seg;Floor;Qty units;Px unit;"
            "Amt loc;Val eur;Ccy pair;Conv fee;Brk fee;Net pay;Tkt\n"
            "20-02-2024;14:15:00;ASML Holding NV;NL0010273215;EAM;XAMS;2;850,00;"
            "-1700,00;-1700,00;;0,00;1,50;-1701,50;tkt-8842\n"
        )
        mock_ai.return_value = AiColumnMappingResult(
            mapped_columns={
                "date": "Tx date",
                "time": "Tx time",
                "product": "Asset title",
                "isin": "ID code",
                "quantity": "Qty units",
                "price": "Px unit",
                "fee": "Brk fee",
                "total": "Net pay",
                "order_id": "Tkt",
            },
            confidence=0.9,
            reasoning="test",
            raw_response="{}",
        )

        result = preview_csv_for_user(self.user, content, platform=PlatformType.DEGIRO)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"]["new"], 1)
        self.assertTrue(result["column_mapping"]["ai_used"])
        self.assertTrue(result["can_confirm_import"])

    def test_coinbase_like_csv_rejected_unsupported(self):
        content = load_text_fixture("csv", "coinbase-like-headers.csv")
        result = preview_csv_for_user(self.user, content)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["failure_reason"], FAILURE_UNSUPPORTED)
        self.assertIn("Timestamp", result["file_headers"])
        self.assertEqual(result["matches"], [])

    def test_coinbase_upload_as_degiro_rejected_mismatch(self):
        content = load_text_fixture("csv", "coinbase-like-headers.csv")
        result = preview_csv_for_user(self.user, content, platform=PlatformType.DEGIRO)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["failure_reason"], "platform_mismatch")


class CsvImportTransparencyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="csv-trust@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def test_partial_import_reports_skipped_rows(self):
        content = load_text_fixture("degiro", "partial-with-unknown-row.csv")
        result = import_csv_for_user(self.user, content, platform=PlatformType.DEGIRO)

        self.assertEqual(result["transactions_imported"], 2)
        self.assertTrue(result["has_import_gaps"])
        self.assertEqual(result["rows_skipped_unrecognized"], 1)
        self.assertTrue(result["skipped_rows"])
        self.assertIn("Onbekende regel", result["unknown_descriptions"][0])
        self.assertEqual(Transaction.objects.filter(portfolio__user=self.user).count(), 2)


class CsvImportAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="csv-api@example.com",
            password="SecurePass123!",
            first_name="Jan",
            auth_0_id="auth0|csv-api",
            email_verified=True,
        )

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_detect_endpoint(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        content = load_bytes_fixture("degiro", "sample-transactions.csv")
        upload = SimpleUploadedFile("t.csv", content, content_type="text/csv")

        response = self.client.post(
            "/api/v1/integrations/csv/detect/",
            {"file": upload},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["recommended"], PlatformType.DEGIRO)

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_preview_endpoint(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        content = load_bytes_fixture("degiro", "sample-transactions.csv")
        upload = SimpleUploadedFile("t.csv", content, content_type="text/csv")

        response = self.client.post(
            "/api/v1/integrations/csv/preview/",
            {"file": upload, "platform": PlatformType.DEGIRO},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "ok")
        self.assertEqual(response.data["data"]["summary"]["new"], 3)

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_generic_import_endpoint(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        content = load_bytes_fixture("degiro", "sample-transactions.csv")
        upload = SimpleUploadedFile("t.csv", content, content_type="text/csv")

        response = self.client.post(
            "/api/v1/integrations/csv/import/",
            {"file": upload, "platform": PlatformType.DEGIRO},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("trust_summary", response.data["data"])
        self.assertEqual(response.data["data"]["transactions_imported"], 3)
