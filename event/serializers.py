from rest_framework import serializers

from member.models import Member
from program.models import Program
from round.models import Round

from .models import Event


class EventSerializer(serializers.ModelSerializer):
    refer_program = serializers.PrimaryKeyRelatedField(
        queryset=Program.objects.all(), required=True, allow_null=False
    )
    rounds = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Round.objects.all(), required=False
    )
    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Member.objects.all(), required=False
    )

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
