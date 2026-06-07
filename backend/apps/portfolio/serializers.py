from decimal import Decimal

from rest_framework import serializers

from apps.portfolio.models import (
    Asset,
    AssetType,
    Portfolio,
    Position,
    Transaction,
    TransactionType,
    VermogensCategorie,
)


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "id",
            "symbol",
            "name",
            "asset_type",
            "category",
        ]


class AssetCategoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ["category"]


class PositionSerializer(serializers.ModelSerializer):
    asset = AssetSerializer(read_only=True)

    class Meta:
        model = Position
        fields = [
            "id",
            "asset",
            "quantity",
            "average_cost_eur",
            "updated_at",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    asset = AssetSerializer(read_only=True)
    import_label = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "asset",
            "transaction_type",
            "quantity",
            "price_eur",
            "fee_eur",
            "total_eur",
            "occurred_at",
            "external_id",
            "source_platform",
            "import_batch_id",
            "import_label",
            "notes",
            "created_at",
        ]

    def get_import_label(self, obj: Transaction) -> str | None:
        batch = obj.import_batch
        if not batch:
            return None
        if batch.source_filename:
            return batch.source_filename
        if batch.source_label:
            return batch.source_label
        return f"Import #{batch.pk}"


class PortfolioSerializer(serializers.ModelSerializer):
    positions_count = serializers.SerializerMethodField()
    transactions_count = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = [
            "id",
            "name",
            "is_default",
            "positions_count",
            "transactions_count",
            "created_at",
            "updated_at",
        ]

    def get_positions_count(self, obj):
        return obj.positions.count()

    def get_transactions_count(self, obj):
        return obj.transactions.count()


class PortfolioDetailSerializer(PortfolioSerializer):
    positions = PositionSerializer(many=True, read_only=True)

    class Meta(PortfolioSerializer.Meta):
        fields = PortfolioSerializer.Meta.fields + ["positions"]


class ManualAssetCreateSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=32)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    asset_type = serializers.ChoiceField(choices=AssetType.choices, default=AssetType.OTHER)
    category = serializers.ChoiceField(
        choices=VermogensCategorie.choices,
        default=VermogensCategorie.BELEGGING,
    )


class ManualTransactionCreateSerializer(serializers.Serializer):
    asset_id = serializers.IntegerField()
    transaction_type = serializers.ChoiceField(choices=TransactionType.choices)
    quantity = serializers.DecimalField(max_digits=24, decimal_places=12)
    price_eur = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        required=False,
        allow_null=True,
    )
    fee_eur = serializers.DecimalField(
        max_digits=18,
        decimal_places=6,
        required=False,
        default=Decimal("0"),
    )
    occurred_at = serializers.DateTimeField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
