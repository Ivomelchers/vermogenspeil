from rest_framework import serializers

from apps.tax.models import Box3BankBalance, Box3Debt, Box3RealEstate


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
            "verhuur_days",
            "verbouw_days",
            "bijtelling_method",
            "economic_rent_yearly_eur",
            "woz_previous_year_eur",
            "bijtelling_rate",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
