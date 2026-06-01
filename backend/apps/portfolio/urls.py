from django.urls import path

from apps.portfolio.views import (
    DashboardSummaryView,
    PortfolioDetailView,
    PortfolioListView,
    PortfolioTransactionsView,
)

urlpatterns = [
    path("portfolios/dashboard/", DashboardSummaryView.as_view(), name="portfolio-dashboard"),
    path("portfolios/", PortfolioListView.as_view(), name="portfolio-list"),
    path("portfolios/<int:portfolio_id>/", PortfolioDetailView.as_view(), name="portfolio-detail"),
    path(
        "portfolios/<int:portfolio_id>/transactions/",
        PortfolioTransactionsView.as_view(),
        name="portfolio-transactions",
    ),
]
