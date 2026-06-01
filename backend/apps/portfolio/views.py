from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.authentication import UnlinkedAuth0User
from apps.accounts.utils.responses import api_error, api_response, first_validation_message
from apps.portfolio.models import Asset, Portfolio
from apps.portfolio.serializers import (
    AssetSerializer,
    ManualAssetCreateSerializer,
    ManualTransactionCreateSerializer,
    PortfolioDetailSerializer,
    PortfolioSerializer,
    TransactionSerializer,
)
from apps.portfolio.services.dashboard import build_dashboard_summary
from apps.portfolio.services.manual import create_manual_asset, create_manual_transaction
from apps.portfolio.services.transactions_list import (
    list_portfolio_transactions,
    parse_page,
    parse_page_size,
    transaction_filter_options,
)


def _linked_user_or_error(request):
    user = request.user
    if isinstance(user, UnlinkedAuth0User):
        return None, api_error(
            message="Account niet gekoppeld. Neem contact op met support.",
            error="account_not_linked",
            status=status.HTTP_403_FORBIDDEN,
        )
    return user, None


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        return api_response(data=build_dashboard_summary(user))


class PortfolioListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        portfolios = Portfolio.objects.for_user(user)
        serializer = PortfolioSerializer(portfolios, many=True)
        return api_response(data=serializer.data)


class PortfolioDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        portfolio = Portfolio.objects.for_user(user).filter(pk=portfolio_id).first()
        if not portfolio:
            return api_error(
                message="Portefeuille niet gevonden.",
                error="not_found",
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PortfolioDetailSerializer(portfolio)
        return api_response(data=serializer.data)


class PortfolioTransactionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        portfolio = Portfolio.objects.for_user(user).filter(pk=portfolio_id).first()
        if not portfolio:
            return api_error(
                message="Portefeuille niet gevonden.",
                error="not_found",
                status=status.HTTP_404_NOT_FOUND,
            )

        page = parse_page(request.query_params.get("page"))
        page_size = parse_page_size(request.query_params.get("page_size"))
        result = list_portfolio_transactions(
            portfolio,
            page=page,
            page_size=page_size,
            sort=request.query_params.get("sort"),
            order=request.query_params.get("order"),
            platform=request.query_params.get("platform"),
            transaction_type=request.query_params.get("transaction_type"),
            symbol=request.query_params.get("symbol"),
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        )
        serializer = TransactionSerializer(result["items"], many=True)
        filters = transaction_filter_options(portfolio)
        return api_response(
            data={
                "items": serializer.data,
                "total": result["total"],
                "page": result["page"],
                "page_size": result["page_size"],
                "total_pages": result["total_pages"],
                "filters": filters,
            }
        )


class ManualAssetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        assets = Asset.objects.for_user(user).order_by("symbol")
        return api_response(data=AssetSerializer(assets, many=True).data)

    def post(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        serializer = ManualAssetCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            asset = create_manual_asset(user, **serializer.validated_data)
        except ValueError as exc:
            return api_error(message=str(exc), error="validation_error", status=status.HTTP_400_BAD_REQUEST)

        return api_response(
            data=AssetSerializer(asset).data,
            message="Asset toegevoegd.",
            status=status.HTTP_201_CREATED,
        )


class ManualTransactionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, portfolio_id):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        portfolio = Portfolio.objects.for_user(user).filter(pk=portfolio_id).first()
        if not portfolio:
            return api_error(
                message="Portefeuille niet gevonden.",
                error="not_found",
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ManualTransactionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            data = serializer.validated_data
            tx = create_manual_transaction(user, portfolio_id=portfolio.id, **data)
        except ValueError as exc:
            return api_error(message=str(exc), error="validation_error", status=status.HTTP_400_BAD_REQUEST)

        return api_response(
            data=TransactionSerializer(tx).data,
            message="Transactie toegevoegd.",
            status=status.HTTP_201_CREATED,
        )
