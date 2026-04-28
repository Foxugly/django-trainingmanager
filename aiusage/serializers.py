from rest_framework import serializers

from .models import AIUsage


class AIUsageDetailSerializer(serializers.ModelSerializer):
    """Single AI call row, with username for display."""

    username = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = AIUsage
        fields = [
            "id",
            "endpoint",
            "model_used",
            "input_tokens",
            "output_tokens",
            "cache_creation_tokens",
            "cache_read_tokens",
            "total_tokens",
            "username",
            "created_at",
        ]
        read_only_fields = fields


class AIUsageAggregateRowSerializer(serializers.Serializer):
    """One row of the aggregated usage response (per period bucket)."""

    period = serializers.CharField()
    total_calls = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    input_tokens = serializers.IntegerField()
    output_tokens = serializers.IntegerField()


class AIUsageAggregateResponseSerializer(serializers.Serializer):
    """Top-level aggregate response."""

    team_id = serializers.IntegerField()
    period = serializers.CharField()
    exclude_ping = serializers.BooleanField()
    data = AIUsageAggregateRowSerializer(many=True)
