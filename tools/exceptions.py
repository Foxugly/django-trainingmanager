from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class ResourceLocked(APIException):
    status_code = 409
    default_detail = _(
        "This resource is locked because it is used in multiple places. Clone it to modify."
    )
    default_code = "resource_locked"


def custom_exception_handler(exc, context):
    """Wrap DRF's default handler to ensure {code, detail} on simple errors.

    DRF preserves `default_code` on APIException subclasses but does not
    surface it in the response body — only `detail`. This wrapper upgrades
    `{detail: "..."}` to `{code: "...", detail: "..."}` when the exception
    carries a default_code. Multi-field ValidationError payloads (the
    `{field: [errors]}` shape) are left untouched to keep DRF semantics.
    """
    response = exception_handler(exc, context)
    if response is None:
        return response

    if (
        isinstance(exc, APIException)
        and isinstance(response.data, dict)
        and "detail" in response.data
        and "code" not in response.data
    ):
        code = getattr(exc, "default_code", None)
        if code:
            response.data = {"code": code, "detail": response.data["detail"]}

    return response
