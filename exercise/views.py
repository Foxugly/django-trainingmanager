from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from team.permissions import IsTrainer
from tools.permissions import AdminWriteAuthRead

from .models import EnergySegment, EnergySystem, Exercise, Modality
from .serializers import (
    EnergySegmentAdminSerializer,
    EnergySegmentSerializer,
    EnergySystemAdminSerializer,
    EnergySystemSerializer,
    ExerciseSerializer,
    ModalityAdminSerializer,
    ModalitySerializer,
)


def _staff_include_inactive(request):
    """Return True iff the request asks for inactive items AND the user is staff."""
    return (
        request.query_params.get("include_inactive") == "true"
        and request.user.is_authenticated
        and request.user.is_staff
    )


class ModalityViewSet(viewsets.ModelViewSet):
    """CRUD on Modality referential, scoped by sport when nested."""

    permission_classes = [AdminWriteAuthRead]
    filterset_fields = ["is_active", "sport", "name"]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Modality.objects.none()

        qs = Modality.objects.all()
        sport_pk = self.kwargs.get("sport_pk")
        if sport_pk:
            qs = qs.filter(sport_id=sport_pk)
        if not _staff_include_inactive(self.request):
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if (
            self.request.user.is_authenticated
            and self.request.user.is_staff
            and self.action in ("create", "update", "partial_update", "retrieve")
        ):
            return ModalityAdminSerializer
        return ModalitySerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class EnergySystemViewSet(viewsets.ModelViewSet):
    """CRUD on EnergySystem referential."""

    permission_classes = [AdminWriteAuthRead]
    filterset_fields = ["is_active", "name"]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return EnergySystem.objects.none()

        qs = EnergySystem.objects.all()
        if not _staff_include_inactive(self.request):
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if (
            self.request.user.is_authenticated
            and self.request.user.is_staff
            and self.action in ("create", "update", "partial_update", "retrieve")
        ):
            return EnergySystemAdminSerializer
        return EnergySystemSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class EnergySegmentViewSet(viewsets.ModelViewSet):
    """CRUD on EnergySegment referential."""

    permission_classes = [AdminWriteAuthRead]
    filterset_fields = ["is_active", "energysystem"]
    search_fields = ["abv", "description"]
    ordering_fields = ["abv", "id"]
    ordering = ["abv"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return EnergySegment.objects.none()

        qs = EnergySegment.objects.select_related("energysystem")
        if not _staff_include_inactive(self.request):
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if (
            self.request.user.is_authenticated
            and self.request.user.is_staff
            and self.action in ("create", "update", "partial_update", "retrieve")
        ):
            return EnergySegmentAdminSerializer
        return EnergySegmentSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class ExerciseViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Exercise."""

    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated, IsTrainer]
    filterset_fields = ["modality", "energysegment", "language"]
    search_fields = ["notes"]
    ordering_fields = ["order", "id", "distance"]
    ordering = ["order"]

    def get_queryset(self):
        from team.utils import scope_by_sport_language

        qs = Exercise.objects.select_related(
            "modality__sport",
            "energysegment__energysystem",
        )
        return scope_by_sport_language(qs, self.request.user, sport_field="modality__sport_id")

    @extend_schema(
        request=None,
        responses={201: ExerciseSerializer},
        description="Clone this Exercise. Returns the new Exercise.",
    )
    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        """Standalone clone : new Exercise with the same scalar fields."""
        original = self.get_object()
        clone = Exercise.objects.create(
            t_start=original.t_start,
            t_break=original.t_break,
            repetition=original.repetition,
            distance=original.distance,
            notes=original.notes,
            modality=original.modality,
            energysegment=original.energysegment,
            language=original.language,
            order=original.order,
        )
        serializer = self.get_serializer(clone)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
