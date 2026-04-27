from rest_framework import viewsets

from .models import Round
from .serializers import RoundSerializer


class RoundViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Round."""
    queryset = Round.objects.all()
    serializer_class = RoundSerializer
    filterset_fields = ['refer_event']
    search_fields = []
    ordering_fields = ['order', 'id']
    ordering = ['refer_event', 'order']
