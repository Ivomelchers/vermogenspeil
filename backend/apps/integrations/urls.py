from django.urls import path

from apps.integrations.csv.views import (
    CsvDetectView,
    CsvImportView,
    CsvPlatformsListView,
    CsvPreviewView,
)
from apps.integrations.views import (
    BitvavoConnectView,
    DegiroCsvImportView,
    DemoFeaturesStatusView,
    DemoSeedView,
    PlatformConnectionDeleteView,
    PlatformConnectionListView,
    PlatformSyncView,
    SyncJobDetailView,
)

urlpatterns = [
    path("connections/", PlatformConnectionListView.as_view(), name="connection-list"),
    path("connections/bitvavo/", BitvavoConnectView.as_view(), name="bitvavo-connect"),
    path(
        "connections/<int:connection_id>/",
        PlatformConnectionDeleteView.as_view(),
        name="connection-delete",
    ),
    path(
        "connections/<int:connection_id>/sync/",
        PlatformSyncView.as_view(),
        name="connection-sync",
    ),
    path("sync-jobs/<int:job_id>/", SyncJobDetailView.as_view(), name="sync-job-detail"),
    path("demo/status/", DemoFeaturesStatusView.as_view(), name="demo-status"),
    path("demo/seed/", DemoSeedView.as_view(), name="demo-seed"),
    path("connections/degiro/import/", DegiroCsvImportView.as_view(), name="degiro-csv-import"),
    path("csv/platforms/", CsvPlatformsListView.as_view(), name="csv-platforms"),
    path("csv/detect/", CsvDetectView.as_view(), name="csv-detect"),
    path("csv/preview/", CsvPreviewView.as_view(), name="csv-preview"),
    path("csv/import/", CsvImportView.as_view(), name="csv-import"),
]
