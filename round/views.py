from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from team.permissions import IsTrainer

from .models import Round
from .serializers import RoundSerializer


class RoundViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Round."""
    queryset = Round.objects.all()
    serializer_class = RoundSerializer
    permission_classes = [IsAuthenticated, IsTrainer]
    filterset_fields = []
    search_fields = []
    ordering_fields = ['order', 'id']
    ordering = ['order']
