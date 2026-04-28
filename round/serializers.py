from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from exercise.models import Exercise
from sport.models import Sport
from sport.serializers import SportSerializer
from tools.exceptions import ResourceLocked

from .models import Round
from .utils import check_exercise_round_consistency


class RoundSerializer(serializers.ModelSerializer):
    sport = SportSerializer(read_only=True)
    sport_id = serializers.PrimaryKeyRelatedField(
        source="sport",
        queryset=Sport.objects.all(),
        write_only=True,
    )
    exercises = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Exercise.objects.all(), required=False
    )
    usage_count = serializers.SerializerMethodField()

    @extend_schema_field(serializers.IntegerField())
    def get_usage_count(self, obj) -> int:
        return obj.usage_count

    class Meta:
        model = Round
        fields = [
            "id",
            "sport",
            "sport_id",
            "language",
            "order",
            "count",
            "t_start",
            "t_break",
            "exercises",
            "usage_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "usage_count", "created_at", "updated_at"]

    def validate(self, data):
        data = super().validate(data)
        exercises = data.get("exercises", [])
        if not exercises:
            return data

        sport = data.get("sport") or (self.instance.sport if self.instance else None)
        language = data.get("language") or (self.instance.language if self.instance else None)
        target = self.instance or Round(sport=sport, language=language)
        if sport is not None:
            target.sport = sport
        if language is not None:
            target.language = language

        for ex in exercises:
            check_exercise_round_consistency(ex, target)
        return data

    def update(self, instance, validated_data):
        if instance.usage_count > 1:
            raise ResourceLocked()
        return super().update(instance, validated_data)
