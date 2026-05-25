from rest_framework.response import Response


def api_response(*, data=None, message="", status=200):
    return Response(
        {"data": data, "error": None, "message": message},
        status=status,
    )


def api_error(*, message, error="error", data=None, status=400):
    return Response(
        {"data": data, "error": error, "message": message},
        status=status,
    )


def first_validation_message(serializer):
    errors = serializer.errors
    for field, messages in errors.items():
        label = field if field == "non_field_errors" else str(field)
        if isinstance(messages, list) and messages:
            return f"{label}: {messages[0]}"
        return f"{label}: {messages}"
    return "Validatie mislukt."
