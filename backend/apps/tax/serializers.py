from rest_framework import serializers

from apps.tax.models import Box3BankBalance, Box3Debt, Box3RealEstate
from apps.tax.services.bijtelling import bijtelling_for_property


class Box3BankBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box3BankBalance
        fields = [
            "id",
            "tax_year",
            "label",
            "account_type",
            "balance_eur",
            "institution",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class Box3DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box3Debt
        fields = [
            "id",
            "tax_year",
            "label",
            "debt_type",
            "outstanding_eur",
            "interest_paid_ytd_eur",
            "creditor",
            "linked_real_estate",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class Box3RealEstateSerializer(serializers.ModelSerializer):
    bijtelling_eur = serializers.SerializerMethodField()
    eigen_gebruik_days_computed = serializers.SerializerMethodField()

    class Meta:
        model = Box3RealEstate
        fields = [
            "id",
            "tax_year",
            "label",
            "property_type",
            "value_eur",
            "is_abroad",
            "annual_rent_eur",
            "vacancy_ratio",
            "rental_income_ytd_eur",
            "eigen_gebruik_days",
            "eigen_gebruik_days_computed",
            "verhuur_days",
            "verbouw_days",
            "bijtelling_method",
            "economic_rent_yearly_eur",
            "woz_previous_year_eur",
            "bijtelling_rate",
            "bijtelling_eur",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "bijtelling_eur", "eigen_gebruik_days_computed", "created_at", "updated_at"]

    def get_bijtelling_eur(self, obj) -> str:
        from decimal import ROUND_HALF_UP, Decimal

        amount = bijtelling_for_property(obj, year=obj.tax_year)
        return format(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")

    def get_eigen_gebruik_days_computed(self, obj) -> int:
        from apps.tax.services.bijtelling import eigen_gebruik_days

        return eigen_gebruik_days(obj)
