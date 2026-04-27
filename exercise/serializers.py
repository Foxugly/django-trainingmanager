from rest_framework import serializers

from tools.exceptions import ResourceLocked

from .models import EnergySegment, EnergySystem, Exercise, Stroke


class StrokeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stroke
        fields = ['id', 'name']
        read_only_fields = ['id']


class EnergySystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergySystem
        fields = ['id', 'name']
        read_only_fields = ['id']


class EnergySegmentSerializer(serializers.ModelSerializer):
    energysystem = serializers.PrimaryKeyRelatedField(
        queryset=EnergySystem.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = EnergySegment
        fields = ['id', 'abv', 'description', 'energysystem']
        read_only_fields = ['id']


class ExerciseSerializer(serializers.ModelSerializer):
    stroke = serializers.PrimaryKeyRelatedField(
        queryset=Stroke.objects.all(), required=False, allow_null=True
    )
    energysegment = serializers.PrimaryKeyRelatedField(
        queryset=EnergySegment.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Exercise
        fields = [
            'id', 'order', 'repetition', 'distance', 'notes',
            't_start', 't_break',
            'stroke', 'energysegment',
            'usage_count',
        ]
        read_only_fields = ['id', 'usage_count']

    def update(self, instance, validated_data):
        if instance.usage_count > 1:
            raise ResourceLocked()
        return super().update(instance, validated_data)
