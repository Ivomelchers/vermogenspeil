from rest_framework import serializers

from apps.snapshots.models import PeilDatumSnapshot


class PeilDatumSnapshotSerializer(serializers.ModelSerializer):
    total_value_eur = serializers.SerializerMethodField()
    valuation_method = serializers.SerializerMethodField()
    peildatum = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()

    class Meta:
        model = PeilDatumSnapshot
        fields = [
            "id",
            "year",
            "peildatum",
            "total_value_eur",
            "valuation_method",
            "is_locked",
            "data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_is_locked(self, obj) -> bool:
        return obj.is_locked

    def get_total_value_eur(self, obj) -> str:
        return obj.data.get("total_value_eur", "0.00")

    def get_valuation_method(self, obj) -> str:
        return obj.data.get("valuation_method", "cost_basis")

    def get_peildatum(self, obj) -> str:
        return obj.data.get("peildatum", "")


class PeilDatumSnapshotCreateSerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=2000, max_value=2100)
