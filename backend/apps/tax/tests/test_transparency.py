from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.tax.services.box3_summary import build_box3_summary
from apps.tax.services.parameters import ensure_default_parameters
from apps.tax.services.transparency import build_tax_warnings

User = get_user_model()


class TaxWarningsTests(TestCase):
    def setUp(self):
        ensure_default_parameters()

    def test_warnings_only_fiscal_parameters(self):
        warnings = build_tax_warnings(
            year=2026,
            forfaitair={"available": True, "parameters_provisional": False},
        )
        self.assertEqual(warnings, [])

    def test_missing_year_parameters_warning(self):
        warnings = build_tax_warnings(year=2099, forfaitair={"available": False})
        self.assertTrue(any("2099" in w for w in warnings))

    def test_box3_summary_has_tax_warnings_not_roadmap(self):
        user = User.objects.create_user(
            email="warn@test.nl",
            password="SecurePass123!",
        )
        summary = build_box3_summary(user, 2026)
        self.assertIn("tax_warnings", summary)
        self.assertNotIn("transparency", summary)
