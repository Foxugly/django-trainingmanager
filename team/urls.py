from rest_framework.routers import DefaultRouter

from .views import TeamJoinRequestViewSet, TeamViewSet

router = DefaultRouter()
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'join-requests', TeamJoinRequestViewSet, basename='joinrequest')

urlpatterns = router.urls
