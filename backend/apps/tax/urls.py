from django.urls import path

from apps.tax.views import ForfaitairBox3View

urlpatterns = [
    path(
        "box3/forfaitair/<int:year>/",
        ForfaitairBox3View.as_view(),
        name="tax-forfaitair-box3",
    ),
]
