from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


def check_exercise_round_consistency(exercise, round_obj):
    """Validate that an exercise can belong to a round.

    Raises a DRF ValidationError on sport or language mismatch. Sport is
    compared via exercise.modality.sport_id (skipped when modality is None).
    """
    if (
        round_obj.sport_id
        and exercise.modality
        and exercise.modality.sport_id != round_obj.sport_id
    ):
        raise serializers.ValidationError(
            {"exercises": _("An exercise has a modality.sport that doesn't match round.sport.")},
            code="exercise_sport_mismatch",
        )

    if round_obj.language and exercise.language != round_obj.language:
        raise serializers.ValidationError(
            {"exercises": _("An exercise has a language that doesn't match round.language.")},
            code="exercise_language_mismatch",
        )
