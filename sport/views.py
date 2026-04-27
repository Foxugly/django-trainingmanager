from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Sport
from .serializers import SportSerializer


class SportViewSet(viewsets.ReadOnlyModelViewSet):
    """Catalogue des sports. Création via admin Django uniquement."""
    queryset = Sport.objects.filter(is_active=True)
    serializer_class = SportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['name', 'slug']
    ordering_fields = ['name']
    ordering = ['name']
