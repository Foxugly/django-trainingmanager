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
        fields = ["id", "order", "count", "t_start", "t_break", "exercises", "usage_count"]
        read_only_fields = ["id", "usage_count"]

    def update(self, instance, validated_data):
        if instance.usage_count > 1:
            raise ResourceLocked()
        return super().update(instance, validated_data)
