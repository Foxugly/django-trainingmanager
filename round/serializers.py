from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from exercise.models import Exercise
from sport.models import Sport
from sport.serializers import SportSerializer
from tools.exceptions import ResourceLocked

from .models import Round


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
        sport = data.get("sport") or (self.instance.sport if self.instance else None)
        language = data.get("language") or (self.instance.language if self.instance else None)
        exercises = data.get("exercises", [])
        if exercises:
            for ex in exercises:
                if sport and ex.modality and ex.modality.sport_id != sport.pk:
                    raise serializers.ValidationError(
                        {
                            "exercises": _(
                                "An exercise has a modality.sport that doesn't match round.sport."
                            )
                        },
                        code="exercise_sport_mismatch",
                    )
                if language and ex.language != language:
                    raise serializers.ValidationError(
                        {
                            "exercises": _(
                                "An exercise has a language that doesn't match round.language."
                            )
                        },
                        code="exercise_language_mismatch",
                    )
        return data

    def update(self, instance, validated_data):
        if instance.usage_count > 1:
            raise ResourceLocked()
        return super().update(instance, validated_data)
