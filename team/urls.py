from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    InvitationLookupView,
    TeamInvitationViewSet,
    TeamJoinRequestViewSet,
    TeamViewSet,
)

router = DefaultRouter()
router.register(r"teams", TeamViewSet, basename="team")
router.register(r"join-requests", TeamJoinRequestViewSet, basename="joinrequest")
router.register(r"invitations", TeamInvitationViewSet, basename="invitation")

urlpatterns = router.urls + [
    path(
        "invitations/lookup/<str:token>/",
        InvitationLookupView.as_view(),
        name="invitation-lookup",
    ),
]
