from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.integrations.csv.ai_column_mapping import AiColumnMappingResult
from apps.integrations.csv.parse_pipeline import parse_csv_with_resolution
from apps.integrations.csv.registry import get_csv_parser
from apps.integrations.degiro.import_service import import_degiro_csv_for_user
from apps.integrations.models import (
    LearnedAliasStatus,
    SharedCsvColumnAlias,
    UserCsvColumnAlias,
)
from apps.integrations.services.learned_aliases import (
    is_safe_learned_mapping,
    record_learned_aliases_from_import,
)
from apps.integrations.testing.fixtures import load_text_fixture

User = get_user_model()

AI_MAP = {
    "date": "Tx date",
    "time": "Tx time",
    "product": "Asset title",
    "isin": "ID code",
    "quantity": "Qty units",
    "price": "Px unit",
    "fee": "Brk fee",
    "total": "Net pay",
    "order_id": "Tkt",
}

NOVEL_CSV = (
    "Tx date;Tx time;Asset title;ID code;Seg;Floor;Qty units;Px unit;"
    "Amt loc;Val eur;Ccy pair;Conv fee;Brk fee;Net pay;Tkt\n"
    "20-02-2024;14:15:00;ASML Holding NV;NL0010273215;EAM;XAMS;2;850,00;"
    "-1700,00;-1700,00;;0,00;1,50;-1701,50;tkt-8842\n"
)


class LearnedAliasSafetyTests(TestCase):
    def test_description_on_fx_ccy_is_unsafe(self):
        self.assertFalse(
            is_safe_learned_mapping(
                "description",
                "FX ccy",
                original_headers={"FX ccy"},
            )
        )

    def test_date_mapping_is_safe(self):
        self.assertTrue(
            is_safe_learned_mapping(
                "date",
                "Trade day",
                original_headers={"Trade day"},
            )
        )


class LearnedAliasFlowTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email="learn-a@example.com",
            password="SecurePass123!",
            first_name="A",
        )
        self.user_b = User.objects.create_user(
            email="learn-b@example.com",
            password="SecurePass123!",
            first_name="B",
        )
        self.content = NOVEL_CSV

    @patch("apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_user_reuses_own_learned_aliases_without_ai(self, mock_ai):
        mock_ai.return_value = AiColumnMappingResult(
            mapped_columns=AI_MAP,
            confidence=0.9,
            reasoning="test",
            raw_response="{}",
        )

        first = import_degiro_csv_for_user(
            self.user_a,
            self.content,
            ai_used=True,
            column_mapping=AI_MAP,
        )
        self.assertEqual(first["transactions_imported"], 1)
        self.assertGreater(UserCsvColumnAlias.objects.filter(user=self.user_a).count(), 0)

        mock_ai.reset_mock()
        mock_ai.return_value = None

        entry = get_csv_parser("degiro")
        headers = self.content.strip().splitlines()[0].split(";")
        _, resolution = parse_csv_with_resolution(
            entry,
            self.content,
            original_headers=headers,
            user=self.user_a,
        )
        self.assertTrue(resolution.learned_user)
        self.assertFalse(resolution.ai_used)
        mock_ai.assert_not_called()

    @patch("apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai")
    @override_settings(
        CSV_AI_COLUMN_MAPPING=True,
        OPENAI_API_KEY="test-key",
        LEARNED_ALIAS_GLOBAL_MIN_USERS=2,
        LEARNED_ALIAS_CRITICAL_MIN_USERS=2,
    )
    def test_shared_alias_requires_two_users(self, mock_ai):
        mock_ai.return_value = AiColumnMappingResult(
            mapped_columns=AI_MAP,
            confidence=0.9,
            reasoning="test",
            raw_response="{}",
        )

        import_degiro_csv_for_user(
            self.user_a,
            self.content,
            ai_used=True,
            column_mapping=AI_MAP,
        )
        shared = SharedCsvColumnAlias.objects.get(
            platform="degiro",
            header_normalized="tx date",
        )
        self.assertEqual(shared.status, LearnedAliasStatus.PENDING)

        mock_ai.reset_mock()
        entry = get_csv_parser("degiro")
        headers = self.content.strip().splitlines()[0].split(";")
        _, resolution_b = parse_csv_with_resolution(
            entry,
            self.content,
            original_headers=headers,
            user=self.user_b,
        )
        self.assertFalse(resolution_b.learned_shared)
        mock_ai.assert_called_once()

        import_degiro_csv_for_user(
            self.user_b,
            self.content,
            ai_used=True,
            column_mapping=AI_MAP,
        )
        shared.refresh_from_db()
        self.assertEqual(shared.status, LearnedAliasStatus.VERIFIED)

        mock_ai.reset_mock()
        user_c = User.objects.create_user(
            email="learn-c@example.com",
            password="SecurePass123!",
            first_name="C",
        )
        _, resolution_c = parse_csv_with_resolution(
            entry,
            self.content,
            original_headers=headers,
            user=user_c,
        )
        self.assertTrue(resolution_c.learned_shared)
        mock_ai.assert_not_called()

    def test_unsafe_description_not_stored_from_batch(self):
        from apps.integrations.degiro.parser import parse_degiro_csv
        from apps.integrations.models import PlatformImportBatch

        user = self.user_a
        parse_result = parse_degiro_csv(self.content, column_mapping=AI_MAP)
        result = import_degiro_csv_for_user(
            user,
            self.content,
            parse_result=parse_result,
            ai_used=True,
            column_mapping=AI_MAP,
        )
        batch = PlatformImportBatch.objects.get(pk=result["import_batch_id"])
        batch.column_mapping = {**AI_MAP, "description": "FX ccy"}
        batch.save(update_fields=["column_mapping", "updated_at"])

        stats = record_learned_aliases_from_import(batch)
        self.assertGreater(stats["user_aliases"], 0)
        self.assertFalse(
            UserCsvColumnAlias.objects.filter(user=user, canonical="description").exists()
        )
