"""
Common — Custom Exception Handler
===================================
Wraps DRF exceptions into the standard API response envelope.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Wrap every error response in the standard envelope:
    { "success": false, "data": null, "message": "...", "errors": {...}, "meta": {} }
    """
    response = exception_handler(exc, context)

    if response is not None:
        errors = response.data if isinstance(response.data, dict) else {"detail": response.data}

        # Extract a human-readable message
        if "detail" in errors:
            message = str(errors.pop("detail"))
        else:
            message = "Validation error."

        response.data = {
            "success": False,
            "data": None,
            "message": message,
            "errors": errors if errors else None,
            "meta": {},
        }

    return response
