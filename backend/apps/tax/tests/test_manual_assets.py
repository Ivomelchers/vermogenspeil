from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.tax.models import Box3BankBalance, Box3Debt, Box3RealEstate
from apps.tax.services.bijtelling import bijtelling_for_property
from apps.tax.services.manual_assets import manual_box3_totals, manual_werkelijk_extras
from apps.tax.services.tax_year import relevant_tax_year

User = get_user_model()


class ManualAssetsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="manual-assets@example.com",
            password="SecurePass123!",
        )
        self.year = relevant_tax_year()

    def test_bank_increases_b(self):
        Box3BankBalance.objects.create(
            user=self.user,
            tax_year=self.year,
            label="ING Spaar",
            balance_eur=Decimal("15000"),
        )
        totals = manual_box3_totals(self.user, self.year)
        self.assertEqual(totals["banktegoeden"], Decimal("15000"))

    def test_debt_increases_s_and_rente_schulden(self):
        Box3Debt.objects.create(
            user=self.user,
            tax_year=self.year,
            label="Hypotheek",
            outstanding_eur=Decimal("100000"),
            interest_paid_ytd_eur=Decimal("2400"),
        )
        totals = manual_box3_totals(self.user, self.year)
        self.assertEqual(totals["schulden"], Decimal("100000"))
        extras = manual_werkelijk_extras(self.user, self.year)
        self.assertEqual(extras["rente_schulden"], Decimal("2400"))

    def test_real_estate_increases_overige_and_huur(self):
        Box3RealEstate.objects.create(
            user=self.user,
            tax_year=self.year,
            label="Vakantiehuis",
            value_eur=Decimal("200000"),
            rental_income_ytd_eur=Decimal("5000"),
        )
        totals = manual_box3_totals(self.user, self.year)
        self.assertEqual(totals["overige_bezittingen"], Decimal("200000"))
        extras = manual_werkelijk_extras(self.user, self.year)
        self.assertEqual(extras["huur"], Decimal("5000"))

    def test_bijtelling_woz_vast(self):
        prop = Box3RealEstate(
            user=self.user,
            tax_year=self.year,
            label="2e woning",
            value_eur=Decimal("280000"),
            woz_previous_year_eur=Decimal("280000"),
            bijtelling_method="woz_vast",
            eigen_gebruik_days=200,
        )
        bijt = bijtelling_for_property(prop, year=self.year)
        self.assertGreater(bijt, Decimal("7000"))
        self.assertLess(bijt, Decimal("8000"))
