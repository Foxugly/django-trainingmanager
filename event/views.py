from rest_framework import viewsets

from .models import Event
from .serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Event."""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filterset_fields = ['refer_agenda', 'date', 'color']
    search_fields = ['name', 'goal']
    ordering_fields = ['date', 'hour_start', 'name', 'id']
    ordering = ['-date', 'hour_start']
