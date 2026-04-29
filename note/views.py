from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from member.models import Member
from team.models import Team
from tools.openapi import INCLUDE_INACTIVE_PARAM

from .models import Note
from .permissions import IsTeamCoachOrReadOwnNotes
from .serializers import NoteSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List coach notes for a member in a team",
        parameters=[INCLUDE_INACTIVE_PARAM],
    ),
    retrieve=extend_schema(parameters=[INCLUDE_INACTIVE_PARAM]),
    update=extend_schema(parameters=[INCLUDE_INACTIVE_PARAM]),
    partial_update=extend_schema(parameters=[INCLUDE_INACTIVE_PARAM]),
)
class NoteViewSet(viewsets.ModelViewSet):
    """CRUD on coach notes within a team-member nested context.

    URL: /api/v1/teams/{team_pk}/members/{member_pk}/notes/
    """

    serializer_class = NoteSerializer
    permission_classes = [IsTeamCoachOrReadOwnNotes]

    def get_team(self):
        team_pk = self.kwargs.get("team_pk")
        if not team_pk:
            return None
        return get_object_or_404(Team, pk=team_pk)

    def get_member_or_none(self):
        member_pk = self.kwargs.get("member_pk")
        if not member_pk:
            return None
        return get_object_or_404(Member, pk=member_pk)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Note.objects.none()

        team = self.get_team()
        member = self.get_member_or_none()
        if team is None or member is None:
            return Note.objects.none()

        qs = Note.objects.filter(team=team, member=member).select_related(
            "author", "team", "member"
        )

        include_inactive = self.request.query_params.get("include_inactive") == "true"
        if not (include_inactive and team.is_managed_by(self.request.user)):
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        team = self.get_team()
        member = self.get_member_or_none()
        if not member.teams.filter(pk=team.pk).exists():
            raise PermissionDenied(_("This member does not belong to this team."))
        serializer.save(team=team, member=member, author=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
