from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from exercise.views import ModalityViewSet

from .views import SportViewSet

router = DefaultRouter()
router.register(r"sports", SportViewSet, basename="sport")

sports_modalities_router = NestedSimpleRouter(router, r"sports", lookup="sport")
sports_modalities_router.register(r"modalities", ModalityViewSet, basename="sport-modalities")

urlpatterns = router.urls + sports_modalities_router.urls
