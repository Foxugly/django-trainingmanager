from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from sport.serializers import SportSerializer
from tools.exceptions import ResourceLocked

from .models import EnergySegment, EnergySystem, Exercise, Modality


class ModalitySerializer(serializers.ModelSerializer):
    sport = SportSerializer(read_only=True)

    class Meta:
        model = Modality
        fields = ["id", "name", "sport"]
        read_only_fields = fields


class EnergySystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergySystem
        fields = ["id", "name"]
        read_only_fields = ["id"]


class EnergySegmentSerializer(serializers.ModelSerializer):
    energysystem = EnergySystemSerializer(read_only=True)
    energysystem_id = serializers.PrimaryKeyRelatedField(
        source="energysystem",
        queryset=EnergySystem.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = EnergySegment
        fields = ["id", "abv", "description", "energysystem", "energysystem_id"]
        read_only_fields = ["id"]


class ExerciseSerializer(serializers.ModelSerializer):
    modality = ModalitySerializer(read_only=True)
    modality_id = serializers.PrimaryKeyRelatedField(
        source="modality",
        queryset=Modality.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    energysegment = EnergySegmentSerializer(read_only=True)
    energysegment_id = serializers.PrimaryKeyRelatedField(
        source="energysegment",
        queryset=EnergySegment.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            "id",
            "order",
            "repetition",
            "distance",
            "notes",
            "t_start",
            "t_break",
            "modality",
            "modality_id",
            "energysegment",
            "energysegment_id",
            "language",
            "usage_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "usage_count", "created_at", "updated_at"]

    @extend_schema_field(serializers.IntegerField())
    def get_usage_count(self, obj) -> int:
        return obj.usage_count

    def update(self, instance, validated_data):
        if instance.usage_count > 1:
            raise ResourceLocked()
        return super().update(instance, validated_data)
