from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from round.models import Round
from sport.serializers import SportSerializer
from tools.exceptions import ResourceLocked
from tools.validators import MMSS_VALIDATOR

from .models import EnergySegment, EnergySystem, Exercise, Modality


class NotAuthorizedRound(PermissionDenied):
    """User has no manager rights on any team owning an event tied to the target round.

    Raised when an Exercise is created with `round_id=<id>` but the round is
    already attached to events whose teams are not managed by the request user.
    Library rounds (no events) skip this check — IsTrainer + (sport, language)
    scoping already protect catalog mutations there.
    """

    default_detail = _("You are not authorized to attach an exercise to this round.")
    default_code = "not_authorized_round"


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
    energy_system = EnergySystemSerializer(source="energysystem", read_only=True)
    energy_system_id = serializers.PrimaryKeyRelatedField(
        source="energysystem",
        queryset=EnergySystem.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = EnergySegment
        fields = [
            "id",
            "abv",
            "description",
            "energy_system",
            "energy_system_id",
            "is_active",
        ]
        read_only_fields = ["id", "is_active"]


class EnergySegmentAdminSerializer(serializers.ModelSerializer):
    """Admin flavor: per-language description variants + writable energy_system_id."""

    energy_system_id = serializers.PrimaryKeyRelatedField(
        source="energysystem",
        queryset=EnergySystem.objects.all(),
    )

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
            "energy_system_id",
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
    # Explicit declaration so drf-spectacular emits `pattern` in the schema.
    t_start = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[MMSS_VALIDATOR],
        help_text=_("MM:SS format, e.g. 1:30."),
    )
    t_break = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[MMSS_VALIDATOR],
        help_text=_("MM:SS format, e.g. 1:30."),
    )
    energysegment = EnergySegmentSerializer(read_only=True)
    energysegment_id = serializers.PrimaryKeyRelatedField(
        source="energysegment",
        queryset=EnergySegment.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    round_id = serializers.PrimaryKeyRelatedField(
        source="_target_round",
        queryset=Round.objects.all(),
        write_only=True,
        required=False,
        help_text=_(
            "Optional. If provided on POST, the newly created Exercise is atomically "
            "attached to this Round. The request user must manage at least one team "
            "of at least one Event linked to this Round (library rounds with no "
            "events are accepted as-is). Ignored on PATCH/PUT."
        ),
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
            "round_id",
            "language",
            "usage_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "usage_count", "created_at", "updated_at"]

    @extend_schema_field(serializers.IntegerField())
    def get_usage_count(self, obj) -> int:
        return obj.usage_count

    def create(self, validated_data):
        target_round = validated_data.pop("_target_round", None)
        if target_round is not None:
            request = self.context.get("request")
            user = getattr(request, "user", None)
            linked_events = list(target_round.event_set.select_related("refer_program__team").all())
            if linked_events:
                authorized = any(
                    e.refer_program is not None and e.refer_program.team.is_managed_by(user)
                    for e in linked_events
                )
                if user is None or not authorized:
                    raise NotAuthorizedRound()
        exercise = super().create(validated_data)
        if target_round is not None:
            target_round.exercises.add(exercise)
        return exercise

    def update(self, instance, validated_data):
        if instance.usage_count > 1:
            raise ResourceLocked()
        validated_data.pop("_target_round", None)
        return super().update(instance, validated_data)
