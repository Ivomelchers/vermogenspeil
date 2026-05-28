from rest_framework.exceptions import AuthenticationFailed


class NoAuthToken(AuthenticationFailed):
    default_detail = "Authorization header ontbreekt."


class InvalidHeader(AuthenticationFailed):
    default_detail = "Ongeldige Authorization header."


class InvalidAuthToken(AuthenticationFailed):
    default_detail = "Ongeldige of verlopen token."
