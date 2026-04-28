"""Shared OpenAPI helpers (drf-spectacular)."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

INCLUDE_INACTIVE_PARAM = OpenApiParameter(
    name="include_inactive",
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "If true and the user is staff, include soft-deleted "
        "(is_active=False) records in the result. Silently ignored "
        "for non-staff users."
    ),
)
