from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from exercise.models import Exercise
from tools.exceptions import ResourceLocked

from .models import Round


class RoundSerializer(serializers.ModelSerializer):
    exercises = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Exercise.objects.all(), required=False
    )

    class Meta:
        model = Round
        fields = [
            "id",
            "sport",
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
        exercises = data.get("exercises", [])
        if sport and exercises:
            for ex in exercises:
                if ex.modality and ex.modality.sport_id != sport.pk:
                    raise serializers.ValidationError(
                        {
                            "exercises": _(
                                "An exercise has a modality.sport that doesn't match round.sport."
                            )
                        },
                        code="exercise_sport_mismatch",
                    )
        return data

    def update(self, instance, validated_data):
        if instance.usage_count > 1:
            raise ResourceLocked()
        return super().update(instance, validated_data)
