from django.urls import path

from apps.tax.views import (
    Box3BankBalanceDetailView,
    Box3BankBalanceListCreateView,
    Box3DebtDetailView,
    Box3DebtListCreateView,
    Box3RealEstateDetailView,
    Box3RealEstateListCreateView,
    Box3ReportView,
    Box3SummaryView,
    ForfaitairBox3View,
    TaxYearContextView,
)

urlpatterns = [
    path("context/", TaxYearContextView.as_view(), name="tax-year-context"),
    # report vóór box3/<year>/ zodat het pad niet door een bredere route wordt onderschept
    path("box3/<int:year>/report/", Box3ReportView.as_view(), name="tax-box3-report"),
    path("box3/forfaitair/<int:year>/", ForfaitairBox3View.as_view(), name="tax-forfaitair-box3"),
    path("box3/<int:year>/", Box3SummaryView.as_view(), name="tax-box3-summary"),
    path("manual/bank-balances/", Box3BankBalanceListCreateView.as_view(), name="tax-bank-balances"),
    path(
        "manual/bank-balances/<int:pk>/",
        Box3BankBalanceDetailView.as_view(),
        name="tax-bank-balance-detail",
    ),
    path("manual/debts/", Box3DebtListCreateView.as_view(), name="tax-debts"),
    path("manual/debts/<int:pk>/", Box3DebtDetailView.as_view(), name="tax-debt-detail"),
    path("manual/real-estate/", Box3RealEstateListCreateView.as_view(), name="tax-real-estate"),
    path("manual/real-estate/<int:pk>/", Box3RealEstateDetailView.as_view(), name="tax-real-estate-detail"),
]
