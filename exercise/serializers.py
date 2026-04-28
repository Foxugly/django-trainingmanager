from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from sport.serializers import SportSerializer
from tools.exceptions import ResourceLocked

from .models import EnergySegment, EnergySystem, Exercise, Modality


class ModalitySerializer(serializers.ModelSerializer):
    sport = SportSerializer(read_only=True)

    class Meta:
        model = Modality
        fields = ["id", "name", "sport", "is_active"]
        read_only_fields = fields


class ModalityAdminSerializer(serializers.ModelSerializer):
    """Admin flavor: per-language name variants + writable sport FK."""

    class Meta:
        model = Modality
        fields = [
            "id",
            "name_fr",
            "name_nl",
            "name_en",
            "name_it",
            "name_es",
            "sport",
            "is_active",
        ]
        read_only_fields = ["id"]


class EnergySystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergySystem
        fields = ["id", "name", "is_active"]
        read_only_fields = ["id", "name", "is_active"]


class EnergySystemAdminSerializer(serializers.ModelSerializer):
    """Admin flavor: per-language name variants."""

    class Meta:
        model = EnergySystem
        fields = [
            "id",
            "name_fr",
            "name_nl",
            "name_en",
            "name_it",
            "name_es",
            "is_active",
        ]
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
        fields = ["id", "abv", "description", "energysystem", "energysystem_id", "is_active"]
        read_only_fields = ["id", "is_active"]


class EnergySegmentAdminSerializer(serializers.ModelSerializer):
    """Admin flavor: per-language description variants + writable energysystem FK."""

    class Meta:
        model = EnergySegment
        fields = [
            "id",
            "abv",
            "description_fr",
            "description_nl",
            "description_en",
            "description_it",
            "description_es",
            "energysystem",
            "is_active",
        ]
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
