from rest_framework import viewsets

from .models import Agenda
from .serializers import AgendaSerializer


class AgendaViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Agenda."""
    queryset = Agenda.objects.all().order_by('name')
    serializer_class = AgendaSerializer
