"""Nested routing for /api/v1/teams/{team_pk}/messages/.

Mirrors the pattern used by note/urls.py: build a local parent chain
so we can plug MessageViewSet under the existing teams URL space
without re-emitting team routes.
"""

from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from team.views import TeamViewSet

from .views import MessageViewSet

_parent = DefaultRouter()
_parent.register(r"teams", TeamViewSet, basename="chat-parent-team")

messages_router = NestedSimpleRouter(_parent, r"teams", lookup="team")
messages_router.register(r"messages", MessageViewSet, basename="team-message")

urlpatterns = messages_router.urls
