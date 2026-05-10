"""Cross-app validators."""

from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ValidationError

# Round.t_start, Round.t_break, Exercise.t_start, Exercise.t_break.
# 1-3 digits of minutes + ':' + exactly 2 digits of seconds (00-59).
# `blank=True` on the fields means the empty string is accepted without
# triggering the validator (Django default behavior).
MMSS_VALIDATOR = RegexValidator(
    regex=r"^\d{1,3}:[0-5]\d$",
    message=_("Expected format: MM:SS (e.g. 1:30)."),
    code="time_mmss_invalid",
)


def validate_reorder_ids(submitted_ids, expected_ids, *, field_name, container_label):
    """Validate a full reorder payload against the existing scope.

    Raises a coded `ValidationError` (handled by the project's custom exception
    handler) on the four failure modes shared by bulk-reorder endpoints
    (Event.rounds_reorder, Round.exercises_reorder, …): empty list, duplicate
    IDs, IDs not in scope, or missing IDs from the expected set.

    Returns the validated list on success.
    """
    if not submitted_ids:
        raise ValidationError(
            detail={"detail": _("{field} cannot be empty.").format(field=field_name)},
            code="empty_list",
        )
    if len(submitted_ids) != len(set(submitted_ids)):
        raise ValidationError(
            detail={"detail": _("{field} contains duplicate IDs.").format(field=field_name)},
            code="duplicate_id",
        )

    submitted = set(submitted_ids)
    expected = set(expected_ids)
    if not submitted.issubset(expected):
        raise ValidationError(
            detail={
                "detail": _("{field} contains IDs not attached to this {container}: {ids}").format(
                    field=field_name,
                    container=container_label,
                    ids=sorted(submitted - expected),
                ),
            },
            code="scope_mismatch",
        )
    if submitted != expected:
        raise ValidationError(
            detail={
                "detail": _("{field} is missing IDs attached to this {container}: {ids}").format(
                    field=field_name,
                    container=container_label,
                    ids=sorted(expected - submitted),
                ),
            },
            code="incomplete_reorder",
        )
    return submitted_ids
