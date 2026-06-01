from django.urls import path

from apps.snapshots.views import (
    PeilDatumSnapshotCreateView,
    PeilDatumSnapshotDetailView,
    PeilDatumSnapshotListView,
)

urlpatterns = [
    path(
        "peildatum/",
        PeilDatumSnapshotListView.as_view(),
        name="peildatum-snapshot-list",
    ),
    path(
        "peildatum/create/",
        PeilDatumSnapshotCreateView.as_view(),
        name="peildatum-snapshot-create",
    ),
    path(
        "peildatum/<int:year>/",
        PeilDatumSnapshotDetailView.as_view(),
        name="peildatum-snapshot-detail",
    ),
]
