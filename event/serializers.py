from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from program.models import Program
from program.serializers import ProgramMinimalSerializer
from round.models import Round

from .models import Event

ADDITIONAL_PROMPT_MAX_LENGTH = 2000


class GenerateTrainingRequestSerializer(serializers.Serializer):
    """Optional payload for POST /events/{id}/generate-training/.

    `additional_prompt` is appended to the LLM user prompt after the
    structured context (sport, level, duration, catalogs). Empty/missing
    is a no-op so older clients without a body remain compatible.
    """

    additional_prompt = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )

    def validate_additional_prompt(self, value):
        # Custom validation (vs. CharField max_length) so we can stamp a
        # specific error code that the frontend can match on, instead of
        # the generic DRF "max_length".
        if len(value) > ADDITIONAL_PROMPT_MAX_LENGTH:
            raise serializers.ValidationError(
                _("Additional prompt cannot exceed %(n)d characters.")
                % {"n": ADDITIONAL_PROMPT_MAX_LENGTH},
                code="additional_prompt_too_long",
            )
        return value


class EventSerializer(serializers.ModelSerializer):
    refer_program = ProgramMinimalSerializer(read_only=True)
    refer_program_id = serializers.PrimaryKeyRelatedField(
        source="refer_program",
        queryset=Program.objects.all(),
        write_only=True,
        required=True,
        allow_null=False,
    )
    rounds = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Round.objects.all(), required=False
    )
    members = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "name",
            "goal",
            "color",
            "date",
            "hour_start",
            "hour_end",
            "total",
            "refer_program",
            "refer_program_id",
            "rounds",
            "members",
            "generated_by_ai",
            "ai_response",
            "ai_generated_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "generated_by_ai",
            "ai_response",
            "ai_generated_at",
            "created_at",
            "updated_at",
        ]
