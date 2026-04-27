from django.utils.translation import gettext_lazy as _
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
        return (
            Member.objects.filter(teams__in=accessible_teams(self.request.user))
            .select_related("user")
            .prefetch_related("teams__sport")
            .distinct()
        )

    def _check_teams_write(self, teams):
        if not teams:
            raise PermissionDenied(_("At least one team is required."))
        manageable = managed_teams(self.request.user)
        for t in teams:
            if not manageable.filter(pk=t.pk).exists():
                raise PermissionDenied(_("You do not manage one of the requested teams."))

    def perform_create(self, serializer):
        self._check_teams_write(serializer.validated_data.get("teams", []))
        serializer.save()

    def perform_update(self, serializer):
        teams = serializer.validated_data.get("teams")
        if teams is not None:
            self._check_teams_write(teams)
        serializer.save()
