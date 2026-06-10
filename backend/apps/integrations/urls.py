from django.urls import path

from apps.integrations.csv.views import (
    CsvDetectView,
    CsvImportView,
    CsvPlatformsListView,
    CsvPreviewView,
)
from apps.integrations.views import (
    BitvavoConnectView,
    BybitConnectView,
    DemoFeaturesStatusView,
    DemoSeedView,
    OkxConnectView,
    PlatformConnectionDeleteView,
    PlatformConnectionListView,
    PlatformConnectionPurgeDataView,
    PlatformImportBatchListView,
    PlatformImportBatchPurgeView,
    PlatformSyncView,
    SyncJobDetailView,
)

urlpatterns = [
    path("connections/", PlatformConnectionListView.as_view(), name="connection-list"),
    path("connections/bitvavo/", BitvavoConnectView.as_view(), name="bitvavo-connect"),
    path("connections/bybit/", BybitConnectView.as_view(), name="bybit-connect"),
    path("connections/okx/", OkxConnectView.as_view(), name="okx-connect"),
    path(
        "connections/<int:connection_id>/",
        PlatformConnectionDeleteView.as_view(),
        name="connection-delete",
    ),
    path(
        "connections/<int:connection_id>/purge-data/",
        PlatformConnectionPurgeDataView.as_view(),
        name="connection-purge-data",
    ),
    path(
        "connections/<int:connection_id>/import-batches/",
        PlatformImportBatchListView.as_view(),
        name="connection-import-batches",
    ),
    path(
        "import-batches/<int:batch_id>/purge/",
        PlatformImportBatchPurgeView.as_view(),
        name="import-batch-purge",
    ),
    path(
        "connections/<int:connection_id>/sync/",
        PlatformSyncView.as_view(),
        name="connection-sync",
    ),
    path("sync-jobs/<int:job_id>/", SyncJobDetailView.as_view(), name="sync-job-detail"),
    path("demo/status/", DemoFeaturesStatusView.as_view(), name="demo-status"),
    path("demo/seed/", DemoSeedView.as_view(), name="demo-seed"),
    path("csv/platforms/", CsvPlatformsListView.as_view(), name="csv-platforms"),
    path("csv/detect/", CsvDetectView.as_view(), name="csv-detect"),
    path("csv/preview/", CsvPreviewView.as_view(), name="csv-preview"),
    path("csv/import/", CsvImportView.as_view(), name="csv-import"),
]
