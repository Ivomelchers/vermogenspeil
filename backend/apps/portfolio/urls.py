from django.urls import path

from apps.portfolio.views import (
    AssetCategoryUpdateView,
    DashboardSummaryView,
    ManualAssetView,
    ManualTransactionCreateView,
    PortfolioDetailView,
    PortfolioListView,
    PortfolioTransactionsExportView,
    PortfolioTransactionsView,
)

urlpatterns = [
    path("portfolios/dashboard/", DashboardSummaryView.as_view(), name="portfolio-dashboard"),
    path("portfolios/", PortfolioListView.as_view(), name="portfolio-list"),
    path("portfolios/assets/", ManualAssetView.as_view(), name="portfolio-manual-asset"),
    path(
        "portfolios/assets/<int:asset_id>/category/",
        AssetCategoryUpdateView.as_view(),
        name="portfolio-asset-category",
    ),
    path("portfolios/<int:portfolio_id>/", PortfolioDetailView.as_view(), name="portfolio-detail"),
    path(
        "portfolios/<int:portfolio_id>/transactions/",
        PortfolioTransactionsView.as_view(),
        name="portfolio-transactions",
    ),
    path(
        "portfolios/<int:portfolio_id>/transactions/export/",
        PortfolioTransactionsExportView.as_view(),
        name="portfolio-transactions-export",
    ),
    path(
        "portfolios/<int:portfolio_id>/transactions/manual/",
        ManualTransactionCreateView.as_view(),
        name="portfolio-manual-transaction",
    ),
]
