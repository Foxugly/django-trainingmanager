from rest_framework import serializers

from exercise.models import Exercise

from .models import Round


class RoundSerializer(serializers.ModelSerializer):
    exercises = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Exercise.objects.all(), required=False
    )

    class Meta:
        model = Round
        fields = ['id', 'order', 'count', 't_start', 't_break', 'exercises']
        read_only_fields = ['id']
