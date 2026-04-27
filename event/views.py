from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from team.queries import accessible_teams, managed_teams

from .models import Event
from .serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Event, scopé par team du program."""
    serializer_class = EventSerializer
    filterset_fields = ['refer_program', 'date', 'color']
    search_fields = ['name', 'goal']
    ordering_fields = ['date', 'hour_start', 'name', 'id']
    ordering = ['-date', 'hour_start']

    def get_queryset(self):
        return Event.objects.filter(
            refer_program__team__in=accessible_teams(self.request.user)
        )

    def _check_program_write(self, program):
        if program is None:
            raise PermissionDenied("refer_program is required.")
        if not managed_teams(self.request.user).filter(pk=program.team_id).exists():
            raise PermissionDenied("You do not manage the team of this program.")

    def perform_create(self, serializer):
        self._check_program_write(serializer.validated_data.get('refer_program'))
        serializer.save()

    def perform_update(self, serializer):
        self._check_program_write(
            serializer.validated_data.get('refer_program', serializer.instance.refer_program)
        )
        serializer.save()
