from rest_framework import serializers

from apps.portfolio.models import Asset, Portfolio, Position, Transaction


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
            "source_platform",
            "created_at",
        ]


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
