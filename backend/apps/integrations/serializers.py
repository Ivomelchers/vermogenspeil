from rest_framework import serializers

from apps.integrations.models import PlatformConnection, PlatformType, SyncJob


class BitvavoConnectSerializer(serializers.Serializer):
    api_key = serializers.CharField(max_length=256, trim_whitespace=True)
    api_secret = serializers.CharField(max_length=256, trim_whitespace=True, write_only=True)
    label = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")


class PlatformConnectionSerializer(serializers.ModelSerializer):
    platform_display = serializers.CharField(source="get_platform_display", read_only=True)
    connection_method_display = serializers.CharField(
        source="get_connection_method_display",
        read_only=True,
    )

    class Meta:
        model = PlatformConnection
        fields = [
            "id",
            "platform",
            "platform_display",
            "connection_method",
            "connection_method_display",
            "label",
            "display_name",
            "status",
            "last_synced_at",
            "last_error",
            "is_active",
            "is_demo",
            "portfolio_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SyncJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncJob
        fields = [
            "id",
            "connection_id",
            "status",
            "positions_synced",
            "transactions_synced",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = fields
