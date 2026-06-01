from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.authentication import UnlinkedAuth0User
from apps.accounts.utils.responses import api_error, api_response, first_validation_message
from apps.tax.models import Box3Debt, Box3RealEstate
from apps.tax.serializers import Box3DebtSerializer, Box3RealEstateSerializer
from apps.tax.services.box3 import build_forfaitair_summary
from apps.tax.services.box3_summary import build_box3_summary
from apps.tax.services.pdf_report import build_box3_pdf
from apps.tax.services.report import build_box3_report
from apps.tax.services.tax_year import tax_year_context


def _linked_user_or_error(request):
    user = request.user
    if isinstance(user, UnlinkedAuth0User):
        return None, api_error(
            message="Account niet gekoppeld. Neem contact op met support.",
            error="account_not_linked",
            status=status.HTTP_403_FORBIDDEN,
        )
    return user, None


class TaxYearContextView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        ctx = tax_year_context()
        ctx["user_active_tax_year"] = user.active_tax_year
        return api_response(data=ctx)


class ForfaitairBox3View(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year: int):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        summary = build_forfaitair_summary(user, year)
        return api_response(data=summary, message=summary.get("message", "Forfaitaire Box 3"))


class Box3SummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year: int):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        summary = build_box3_summary(user, year)
        return api_response(data=summary, message=f"Box 3 {year} samenvatting")


class Box3ReportView(APIView):
    permission_classes = [IsAuthenticated]

    def perform_content_negotiation(self, request, force=False):
        """PDF-export retourneert ruwe HttpResponse; sla DRF negotiation over."""
        if request.query_params.get("export", "").lower() == "pdf":
            return (None, None)
        return super().perform_content_negotiation(request, force)

    def get(self, request, year: int):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        report = build_box3_report(user, year, include_werkelijk=True)
        # Gebruik `export`, niet `format` — DRF reserveert ?format= voor content negotiation.
        export = (request.query_params.get("export") or "json").lower()

        if export == "pdf":
            pdf_bytes = build_box3_pdf(report)
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="box3-rapport-{year}.pdf"'
            return response

        return api_response(data=report, message=f"Box 3 rapport {year}")


class Box3DebtListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        year = request.query_params.get("year")
        qs = Box3Debt.objects.filter(user=user)
        if year:
            qs = qs.filter(tax_year=int(year))
        return api_response(data=Box3DebtSerializer(qs, many=True).data)

    def post(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        serializer = Box3DebtSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        debt = serializer.save(user=user)
        return api_response(
            data=Box3DebtSerializer(debt).data,
            message="Schuld toegevoegd.",
            status=status.HTTP_201_CREATED,
        )


class Box3DebtDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_debt(self, user, pk):
        return Box3Debt.objects.filter(user=user, pk=pk).first()

    def patch(self, request, pk: int):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        debt = self._get_debt(user, pk)
        if not debt:
            return api_error(message="Schuld niet gevonden.", error="not_found", status=404)
        serializer = Box3DebtSerializer(debt, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=400,
            )
        serializer.save()
        return api_response(data=serializer.data, message="Schuld bijgewerkt.")

    def delete(self, request, pk: int):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        debt = self._get_debt(user, pk)
        if not debt:
            return api_error(message="Schuld niet gevonden.", error="not_found", status=404)
        debt.delete()
        return api_response(message="Schuld verwijderd.")


class Box3RealEstateListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        year = request.query_params.get("year")
        qs = Box3RealEstate.objects.filter(user=user)
        if year:
            qs = qs.filter(tax_year=int(year))
        return api_response(data=Box3RealEstateSerializer(qs, many=True).data)

    def post(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        serializer = Box3RealEstateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        prop = serializer.save(user=user)
        return api_response(
            data=Box3RealEstateSerializer(prop).data,
            message="Vastgoed toegevoegd.",
            status=status.HTTP_201_CREATED,
        )


class Box3RealEstateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_property(self, user, pk):
        return Box3RealEstate.objects.filter(user=user, pk=pk).first()

    def patch(self, request, pk: int):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        prop = self._get_property(user, pk)
        if not prop:
            return api_error(message="Vastgoed niet gevonden.", error="not_found", status=404)
        serializer = Box3RealEstateSerializer(prop, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=400,
            )
        serializer.save()
        return api_response(data=serializer.data, message="Vastgoed bijgewerkt.")

    def delete(self, request, pk: int):
        user, error = _linked_user_or_error(request)
        if error:
            return error
        prop = self._get_property(user, pk)
        if not prop:
            return api_error(message="Vastgoed niet gevonden.", error="not_found", status=404)
        prop.delete()
        return api_response(message="Vastgoed verwijderd.")
