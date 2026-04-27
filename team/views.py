from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Team
from .permissions import IsTeamOwnerOrReadOnly
from .serializers import TeamSerializer


class TeamViewSet(viewsets.ModelViewSet):
    """CRUD sur Teams. Liste = teams gérées par l'user + teams publiques actives."""
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsTeamOwnerOrReadOnly]
    filterset_fields = ['is_active', 'is_public']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        user = self.request.user
        return Team.objects.filter(
            Q(owner=user)
            | Q(managers=user)
            | Q(is_public=True, is_active=True)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
