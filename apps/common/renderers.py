"""
Common — API Response Renderer
================================
Wraps all successful DRF responses in the standard envelope.
"""
from rest_framework.renderers import JSONRenderer


class ApiRenderer(JSONRenderer):
    """
    Wraps every successful response into the envelope:
    { "success": true, "data": ..., "message": ..., "errors": null, "meta": {} }

    If the view already returns an envelope (has a "success" key), it passes through.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        # Don't wrap if the data is already enveloped or if it's an error
        if isinstance(data, dict) and "success" in data:
            return super().render(data, accepted_media_type, renderer_context)

        # Don't wrap error responses — the exception handler handles those
        if response is not None and response.status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)

        envelope = {
            "success": True,
            "data": data,
            "message": None,
            "errors": None,
            "meta": {},
        }

        return super().render(envelope, accepted_media_type, renderer_context)
