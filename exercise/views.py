from rest_framework import viewsets

from .models import EnergySegment, EnergySystem, Exercise, Stroke
from .serializers import (
    EnergySegmentSerializer,
    EnergySystemSerializer,
    ExerciseSerializer,
    StrokeSerializer,
)


class StrokeViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule pour Stroke (référentiel)."""
    queryset = Stroke.objects.all().order_by('name')
    serializer_class = StrokeSerializer


class EnergySystemViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule pour EnergySystem (référentiel)."""
    queryset = EnergySystem.objects.all().order_by('pk')
    serializer_class = EnergySystemSerializer


class EnergySegmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule pour EnergySegment (référentiel)."""
    queryset = EnergySegment.objects.all().order_by('pk')
    serializer_class = EnergySegmentSerializer


class ExerciseViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Exercise."""
    queryset = Exercise.objects.all().order_by('refer_round', 'order')
    serializer_class = ExerciseSerializer
