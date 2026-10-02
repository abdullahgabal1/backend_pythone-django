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
        if isinstance(response.data, list):
            errors = {"detail": response.data}
        elif isinstance(response.data, dict):
            errors = response.data
        else:
            errors = {"detail": str(response.data)}

        # Extract a human-readable message
        message = "Validation error."
        if "detail" in errors:
            detail = errors.pop("detail")
            if isinstance(detail, list) and len(detail) > 0:
                message = str(detail[0])
            else:
                message = str(detail)

        response.data = {
            "success": False,
            "data": None,
            "message": message,
            "errors": errors if errors else None,
            "meta": {},
        }

    return response
