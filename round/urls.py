from rest_framework.routers import DefaultRouter

from .views import RoundViewSet

router = DefaultRouter()
router.register(r"rounds", RoundViewSet, basename="round")

urlpatterns = router.urls
