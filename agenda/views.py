from rest_framework import viewsets

from .models import Agenda
from .serializers import AgendaSerializer


class AgendaViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Agenda."""
    queryset = Agenda.objects.all()
    serializer_class = AgendaSerializer
    filterset_fields = ['name', 'date_start', 'date_end']
    search_fields = ['name']
    ordering_fields = ['name', 'date_start', 'date_end']
    ordering = ['name']
