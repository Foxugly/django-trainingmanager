from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from .views import (
    InvitationLookupView,
    TeamInvitationViewSet,
    TeamJoinRequestViewSet,
    TeamMembershipViewSet,
    TeamViewSet,
)

router = DefaultRouter()
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"join-requests", TeamJoinRequestViewSet, basename="joinrequest")
router.register(r"invitations", TeamInvitationViewSet, basename="invitation")

memberships_router = NestedSimpleRouter(router, r"teams", lookup="team")
memberships_router.register(r"memberships", TeamMembershipViewSet, basename="team-membership")

urlpatterns = (
    router.urls
    + memberships_router.urls
    + [
        path(
            "invitations/lookup/<str:token>/",
            InvitationLookupView.as_view(),
            name="invitation-lookup",
        ),
    ]
)
