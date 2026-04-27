from rest_framework.routers import DefaultRouter

from .views import (
    EnergySegmentViewSet,
    EnergySystemViewSet,
    ExerciseViewSet,
)

router = DefaultRouter()
router.register(r"exercises", ExerciseViewSet, basename="exercise")
router.register(r"energy-systems", EnergySystemViewSet, basename="energy-system")
router.register(r"energy-segments", EnergySegmentViewSet, basename="energy-segment")

urlpatterns = router.urls
