"""Cross-app validators."""

from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

# Round.t_start, Round.t_break, Exercise.t_start, Exercise.t_break.
# 1-3 digits of minutes + ':' + exactly 2 digits of seconds (00-59).
# `blank=True` on the fields means the empty string is accepted without
# triggering the validator (Django default behavior).
MMSS_VALIDATOR = RegexValidator(
    regex=r"^\d{1,3}:[0-5]\d$",
    message=_("Expected format: MM:SS (e.g. 1:30)."),
    code="time_mmss_invalid",
)
