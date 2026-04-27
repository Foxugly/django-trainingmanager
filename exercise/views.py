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
    queryset = Stroke.objects.all()
    serializer_class = StrokeSerializer
    filterset_fields = ['name']
    search_fields = ['name']
    ordering_fields = ['name', 'id']
    ordering = ['name']


class EnergySystemViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule pour EnergySystem (référentiel)."""
    queryset = EnergySystem.objects.all()
    serializer_class = EnergySystemSerializer
    filterset_fields = ['name']
    search_fields = ['name']
    ordering_fields = ['name', 'id']
    ordering = ['name']


class EnergySegmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule pour EnergySegment (référentiel)."""
    queryset = EnergySegment.objects.all()
    serializer_class = EnergySegmentSerializer
    filterset_fields = ['energysystem']
    search_fields = ['abv', 'description']
    ordering_fields = ['id']
    ordering = ['pk']


class ExerciseViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Exercise."""
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
    filterset_fields = ['refer_round', 'stroke', 'energysegment']
    search_fields = ['notes']
    ordering_fields = ['order', 'id', 'distance']
    ordering = ['refer_round', 'order']
