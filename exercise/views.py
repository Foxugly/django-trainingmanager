from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from team.permissions import IsTrainer

from .models import EnergySegment, EnergySystem, Exercise, Modality
from .serializers import (
    EnergySegmentSerializer,
    EnergySystemSerializer,
    ExerciseSerializer,
    ModalitySerializer,
)


class ModalityViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule pour Modality (référentiel par sport, nested via /sports/<id>/modalities/)."""

    serializer_class = ModalitySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]

    def get_queryset(self):
        sport_id = self.kwargs.get("sport_pk")
        qs = Modality.objects.all()
        if sport_id:
            qs = qs.filter(sport_id=sport_id)
        return qs


class EnergySystemViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule pour EnergySystem (référentiel)."""

    queryset = EnergySystem.objects.all()
    serializer_class = EnergySystemSerializer
    filterset_fields = ["name"]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]
    ordering = ["name"]


class EnergySegmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule pour EnergySegment (référentiel)."""

    queryset = EnergySegment.objects.all()
    serializer_class = EnergySegmentSerializer
    filterset_fields = ["energysystem"]
    search_fields = ["abv", "description"]
    ordering_fields = ["id"]
    ordering = ["pk"]


class ExerciseViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Exercise."""

    queryset = Exercise.objects.select_related(
        "modality__sport",
        "energysegment__energysystem",
    )
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated, IsTrainer]
    filterset_fields = ["modality", "energysegment"]
    search_fields = ["notes"]
    ordering_fields = ["order", "id", "distance"]
    ordering = ["order"]

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
            order=original.order,
        )
        serializer = self.get_serializer(clone)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
