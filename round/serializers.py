from rest_framework import serializers

from event.models import Event
from exercise.models import Exercise

from .models import Round


class RoundSerializer(serializers.ModelSerializer):
    refer_event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(), required=False, allow_null=True
    )
    exercises = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Exercise.objects.all(), required=False
    )

    class Meta:
        model = Round
        fields = ['id', 'order', 'count', 't_start', 't_break', 'refer_event', 'exercises']
        read_only_fields = ['id']
