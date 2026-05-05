from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from team.queries import managed_teams, user_member_teams

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
            Member.objects.filter(
                memberships__team__in=user_member_teams(self.request.user),
                memberships__left_at__isnull=True,
            )
            .select_related("user")
            .prefetch_related("memberships__team__sport")
            .distinct()
        )

    def _check_user_manages_a_team(self):
        if not managed_teams(self.request.user).exists():
            raise PermissionDenied(_("You must manage at least one team to create members."))

    def perform_create(self, serializer):
        self._check_user_manages_a_team()
        serializer.save()

    def perform_update(self, serializer):
        self._check_user_manages_a_team()
        serializer.save()
