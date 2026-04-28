from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException, ErrorDetail, ValidationError
from rest_framework.views import exception_handler


class ResourceLocked(APIException):
    status_code = 409
    default_detail = _(
        "This resource is locked because it is used in multiple places. Clone it to modify."
    )
    default_code = "resource_locked"


def custom_exception_handler(exc, context):
    """Normalise every 4xx error to {code, detail, fields?}.

    - APIException subclasses with default_code -> {code, detail}.
    - ValidationError dict (multi-field) -> {code, detail, fields}.
    - ValidationError list/str -> {code, detail}.
    - DRF builtins (NotAuthenticated, PermissionDenied, NotFound,
      MethodNotAllowed, Throttled, AuthenticationFailed, ...) carry
      default_code, so they fall under the APIException branch.
    """
    response = exception_handler(exc, context)
    if response is None:
        return response

    if isinstance(exc, ValidationError):
        response.data = _normalize_validation_error(exc.detail)
        return response

    if isinstance(exc, APIException) and isinstance(response.data, dict):
        if "detail" in response.data and "code" not in response.data:
            code = getattr(exc, "default_code", None)
            if code:
                response.data = {"code": code, "detail": response.data["detail"]}

    return response


def _normalize_validation_error(detail):
    if isinstance(detail, ErrorDetail) or isinstance(detail, str):
        return {"code": "validation_error", "detail": str(detail)}

    if isinstance(detail, list):
        if not detail:
            return {"code": "validation_error", "detail": str(_("Validation failed."))}
        return {"code": "validation_error", "detail": str(detail[0])}

    if isinstance(detail, dict):
        # APIException-like dict: {"detail": "...", "code"?: "..."}
        # raised via raise serializers.ValidationError({"detail": "..."}).
        if set(detail.keys()) <= {"detail", "code"}:
            inner = detail.get("detail")
            inner_str = str(inner[0]) if isinstance(inner, list) and inner else str(inner)
            inner_code = detail.get("code")
            if isinstance(inner, ErrorDetail) and not inner_code:
                inner_code = inner.code
            return {
                "code": str(inner_code) if inner_code else "validation_error",
                "detail": inner_str,
            }

        fields = {name: _normalize_field_errors(errs) for name, errs in detail.items()}
        return {
            "code": "validation_error",
            "detail": str(_("Some fields are invalid.")),
            "fields": fields,
        }

    return {"code": "validation_error", "detail": str(detail)}


def _normalize_field_errors(errors):
    if not isinstance(errors, list):
        errors = [errors]
    out = []
    for err in errors:
        if isinstance(err, ErrorDetail):
            out.append({"code": err.code or "invalid", "detail": str(err)})
        elif isinstance(err, dict):
            out.append(
                {
                    "code": str(err.get("code", "invalid")),
                    "detail": str(err.get("detail", err)),
                }
            )
        else:
            out.append({"code": "invalid", "detail": str(err)})
    return out
