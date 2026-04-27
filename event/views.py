from rest_framework import viewsets

from .models import Event
from .serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Event."""
    queryset = Event.objects.all().order_by('-date', 'hour_start')
    serializer_class = EventSerializer
