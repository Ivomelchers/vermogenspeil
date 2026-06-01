from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.authentication import UnlinkedAuth0User
from apps.accounts.utils.responses import api_error, api_response
from apps.tax.services.box3 import build_forfaitair_summary


def _linked_user_or_error(request):
    user = request.user
    if isinstance(user, UnlinkedAuth0User):
        return None, api_error(
            message="Account niet gekoppeld. Neem contact op met support.",
            error="account_not_linked",
            status=status.HTTP_403_FORBIDDEN,
        )
    return user, None


class ForfaitairBox3View(APIView):
    """GET forfaitaire Box 3-berekening voor een belastingjaar (vereist peildatum-snapshot)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, year: int):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        summary = build_forfaitair_summary(user, year)
        if not summary.get("available"):
            return api_response(
                data=summary,
                message=summary.get("message", "Berekening niet beschikbaar."),
            )

        return api_response(
            data=summary,
            message=f"Forfaitaire Box 3 {year} berekend.",
        )
