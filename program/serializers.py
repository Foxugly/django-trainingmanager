from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from event.models import Event
from team.models import Team
from team.serializers import TeamMinimalSerializer

from .choices import OVERLAP_STRATEGY_CHOICES
from .models import Program


class ProgramMinimalSerializer(serializers.ModelSerializer):
    """Compact program payload for nested read contexts."""

    class Meta:
        model = Program
        fields = ["id", "name"]
        read_only_fields = fields


class ProgramSerializer(serializers.ModelSerializer):
    team = TeamMinimalSerializer(read_only=True)
    team_id = serializers.PrimaryKeyRelatedField(
        source="team",
        queryset=Team.objects.all(),
        write_only=True,
    )
    events = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Event.objects.all(), required=False
    )

    def __init__(self, *args, **kwargs):
        # C4 fix: scope the writable `events` queryset to events of teams the
        # requesting user manages. Without this, a manager of team A could
        # PATCH a Program of team A to attach Events belonging to team B,
        # crossing the team-scoped boundary.
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request is None or not getattr(request.user, "is_authenticated", False):
            return
        from team.queries import managed_teams

        self.fields["events"].child_relation.queryset = Event.objects.filter(
            refer_program__team__in=managed_teams(request.user)
        )

    class Meta:
        model = Program
        fields = [
            "id",
            "name",
            "date_start",
            "date_end",
            "team",
            "team_id",
            "events",
            "frequency_per_week",
            "description",
            "generated_by_ai",
            "ai_response",
            "ai_generated_at",
            "is_active",
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


ADDITIONAL_PROMPT_MAX_LENGTH = 2000


class GeneratePlanRequestSerializer(serializers.Serializer):
    date_start = serializers.DateField()
    date_end = serializers.DateField()
    frequency_per_week = serializers.IntegerField(min_value=1, max_value=14)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    additional_prompt = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )
    overlap_strategy = serializers.ChoiceField(
        choices=OVERLAP_STRATEGY_CHOICES,
        default="add_only",
    )

    def validate_additional_prompt(self, value):
        if len(value) > ADDITIONAL_PROMPT_MAX_LENGTH:
            raise serializers.ValidationError(
                _("Additional prompt cannot exceed %(n)d characters.")
                % {"n": ADDITIONAL_PROMPT_MAX_LENGTH},
                code="additional_prompt_too_long",
            )
        return value

    def validate(self, data):
        if data["date_end"] < data["date_start"]:
            raise serializers.ValidationError(
                {"date_end": _("date_end must be after date_start.")},
                code="date_range_invalid",
            )
        if (data["date_end"] - data["date_start"]).days > 365:
            raise serializers.ValidationError(
                {"date_end": _("Range cannot exceed 365 days.")},
                code="date_range_too_long",
            )
        return data
