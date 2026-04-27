from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from team.queries import accessible_teams, managed_teams

from .models import Agenda
from .serializers import AgendaSerializer


class AgendaViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Agenda, scopé par team."""
    serializer_class = AgendaSerializer
    filterset_fields = ['name', 'date_start', 'date_end', 'team']
    search_fields = ['name']
    ordering_fields = ['name', 'date_start', 'date_end']
    ordering = ['name']

    def get_queryset(self):
        return Agenda.objects.filter(
            team__in=accessible_teams(self.request.user)
        )

    def _check_team_write(self, team):
        if team is None or not managed_teams(self.request.user).filter(pk=team.pk).exists():
            raise PermissionDenied("You do not manage this team.")

    def perform_create(self, serializer):
        self._check_team_write(serializer.validated_data.get('team'))
        serializer.save()

    def perform_update(self, serializer):
        self._check_team_write(serializer.validated_data.get('team', serializer.instance.team))
        serializer.save()
