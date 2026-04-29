"""Nested routing for /api/v1/teams/{team_pk}/members/{member_pk}/notes/.

We rebuild a parent->child router chain locally so we can plug the
NoteViewSet under teams/members without touching team/urls.py or
member/urls.py. The parent registrations use unique basenames to
avoid collisions with the existing routes (which are still served
by their respective apps).

Only `notes_router.urls` is exported, so this module adds ONLY the
note URL patterns (no duplicate teams/ or members/ routes).
"""

from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from member.views import MemberViewSet
from team.views import TeamViewSet

from .views import NoteViewSet

_parent = DefaultRouter()
_parent.register(r"teams", TeamViewSet, basename="note-parent-team")

_members_router = NestedSimpleRouter(_parent, r"teams", lookup="team")
_members_router.register(r"members", MemberViewSet, basename="note-parent-member")

notes_router = NestedSimpleRouter(_members_router, r"members", lookup="member")
notes_router.register(r"notes", NoteViewSet, basename="member-note")

urlpatterns = notes_router.urls
