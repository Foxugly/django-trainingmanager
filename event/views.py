from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from team.queries import accessible_teams, managed_teams

from .models import Event
from .serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Event, scopé par team de l'agenda."""
    serializer_class = EventSerializer
    filterset_fields = ['refer_agenda', 'date', 'color']
    search_fields = ['name', 'goal']
    ordering_fields = ['date', 'hour_start', 'name', 'id']
    ordering = ['-date', 'hour_start']

    def get_queryset(self):
        return Event.objects.filter(
            refer_agenda__team__in=accessible_teams(self.request.user)
        )

    def _check_agenda_write(self, agenda):
        if agenda is None:
            raise PermissionDenied("refer_agenda is required.")
        if not managed_teams(self.request.user).filter(pk=agenda.team_id).exists():
            raise PermissionDenied("You do not manage the team of this agenda.")

    def perform_create(self, serializer):
        self._check_agenda_write(serializer.validated_data.get('refer_agenda'))
        serializer.save()

    def perform_update(self, serializer):
        self._check_agenda_write(
            serializer.validated_data.get('refer_agenda', serializer.instance.refer_agenda)
        )
        serializer.save()
