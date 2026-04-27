from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from team.queries import accessible_teams, managed_teams

from .models import Member
from .serializers import MemberSerializer


class MemberViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Member, scopé par teams du Member."""

    serializer_class = MemberSerializer
    filterset_fields = ["lastname", "firstname"]
    search_fields = ["firstname", "lastname", "email"]
    ordering_fields = ["lastname", "firstname", "id"]
    ordering = ["lastname", "firstname"]

    def get_queryset(self):
        return Member.objects.filter(teams__in=accessible_teams(self.request.user)).distinct()

    def _check_teams_write(self, teams):
        if not teams:
            raise PermissionDenied("At least one team is required.")
        manageable = managed_teams(self.request.user)
        for t in teams:
            if not manageable.filter(pk=t.pk).exists():
                raise PermissionDenied(f"You do not manage team {t.pk}.")

    def perform_create(self, serializer):
        self._check_teams_write(serializer.validated_data.get("teams", []))
        serializer.save()

    def perform_update(self, serializer):
        teams = serializer.validated_data.get("teams")
        if teams is not None:
            self._check_teams_write(teams)
        serializer.save()
