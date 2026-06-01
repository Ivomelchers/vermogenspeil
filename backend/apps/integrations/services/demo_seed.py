from django.conf import settings

from apps.integrations.models import (
    ConnectionMethod,
    PlatformConnection,
    PlatformType,
    SyncJob,
    SyncStatus,
)
from apps.integrations.services.sync import run_connection_sync
from apps.portfolio.services import get_or_create_default_portfolio

DEMO_SPECS = (
    {
        "platform": PlatformType.BITVAVO,
        "label": "Bitvavo (demo)",
        "connection_method": ConnectionMethod.API,
    },
    {
        "platform": PlatformType.DEGIRO,
        "label": "DEGIRO (demo)",
        "connection_method": ConnectionMethod.CSV,
    },
)


def demo_features_enabled() -> bool:
    return getattr(settings, "DEMO_FEATURES_ENABLED", False)


def seed_demo_for_user(user) -> dict:
    if not demo_features_enabled():
        raise PermissionError("Demo-functies zijn uitgeschakeld.")

    portfolio = get_or_create_default_portfolio(user)
    connections_data = []
    total_positions = 0
    total_transactions = 0

    for spec in DEMO_SPECS:
        connection, _ = PlatformConnection.objects.update_or_create(
            user=user,
            platform=spec["platform"],
            label=spec["label"],
            defaults={
                "portfolio": portfolio,
                "connection_method": spec["connection_method"],
                "is_demo": True,
                "is_active": True,
                "api_key_encrypted": "",
                "api_secret_encrypted": "",
                "last_error": "",
                "status": SyncStatus.PENDING,
            },
        )
        connection.is_demo = True
        connection.is_active = True
        connection.portfolio = portfolio
        connection.connection_method = spec["connection_method"]
        connection.save()

        sync_job = SyncJob.objects.create(connection=connection, status=SyncStatus.PENDING)
        run_connection_sync(sync_job.id)

        sync_job.refresh_from_db()
        connection.refresh_from_db()
        total_positions += sync_job.positions_synced
        total_transactions += sync_job.transactions_synced

        connections_data.append(
            {
                "id": connection.id,
                "label": connection.display_name,
                "platform": connection.platform,
                "status": connection.status,
                "positions_synced": sync_job.positions_synced,
                "transactions_synced": sync_job.transactions_synced,
            }
        )

    return {
        "portfolio_id": portfolio.id,
        "connections": connections_data,
        "positions_synced": total_positions,
        "transactions_synced": total_transactions,
    }
