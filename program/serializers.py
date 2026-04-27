from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from event.models import Event
from member.models import Member

from .models import Program


class ProgramSerializer(serializers.ModelSerializer):
    events = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Event.objects.all(), required=False
    )
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Member.objects.all(), required=False
    )

    class Meta:
        model = Program
        fields = [
            "id",
            "name",
            "date_start",
            "date_end",
            "team",
            "events",
            "members",
            "frequency_per_week",
            "description",
            "generated_by_ai",
            "ai_prompt",
            "ai_response",
            "ai_generated_at",
        ]
        read_only_fields = [
            "id",
            "generated_by_ai",
            "ai_prompt",
            "ai_response",
            "ai_generated_at",
        ]


class GeneratePlanRequestSerializer(serializers.Serializer):
    date_start = serializers.DateField()
    date_end = serializers.DateField()
    frequency_per_week = serializers.IntegerField(min_value=1, max_value=14)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    overlap_strategy = serializers.ChoiceField(
        choices=["add_only", "merge", "replace"],
        default="add_only",
    )

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
