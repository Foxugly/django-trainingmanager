from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from exercise.models import Exercise
from exercise.serializers import ExerciseSerializer
from team.permissions import IsTrainer
from team.utils import scope_by_sport_language

from .models import Round
from .serializers import RoundSerializer


class RoundViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Round."""

    serializer_class = RoundSerializer
    permission_classes = [IsAuthenticated, IsTrainer]
    filterset_fields = ["sport", "language"]
    search_fields = []
    ordering_fields = ["order", "id"]
    ordering = ["order"]

    def get_queryset(self):
        qs = Round.objects.select_related("sport").prefetch_related(
            "exercises__modality__sport",
            "exercises__energysegment__energysystem",
        )
        return scope_by_sport_language(qs, self.request.user, sport_field="sport_id")

    @extend_schema(
        request=None,
        responses={201: RoundSerializer},
        description="Clone this Round (scalar fields + M2M exercises). Returns the new Round.",
    )
    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        """Standalone clone : new Round with the same scalar fields and the
        same exercise list (M2M copied)."""
        original = self.get_object()
        clone = Round.objects.create(
            sport=original.sport,
            language=original.language,
            count=original.count,
            t_start=original.t_start,
            t_break=original.t_break,
            order=original.order,
        )
        clone.exercises.set(original.exercises.all())
        serializer = self.get_serializer(clone)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=inline_serializer(
            name="CloneExerciseRequest",
            fields={"exercise_id": serializers.IntegerField()},
        ),
        responses={
            201: ExerciseSerializer,
            400: None,
            404: None,
        },
        description="Clone an Exercise and attach the copy to this Round.",
    )
    @action(detail=True, methods=["post"], url_path="clone-exercise")
    def clone_exercise(self, request, pk=None):
        """Clone an Exercise and attach it to this Round.
        Body: {"exercise_id": <id>}."""
        round_obj = self.get_object()
        exercise_id = request.data.get("exercise_id")
        if not exercise_id:
            return Response(
                {"code": "exercise_id_required", "detail": _("exercise_id is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        scoped_qs = Exercise.objects.filter(
            modality__sport_id=round_obj.sport_id,
            language=round_obj.language,
        )
        try:
            original = scoped_qs.get(pk=exercise_id)
        except Exercise.DoesNotExist:
            return Response(
                {
                    "code": "exercise_not_found",
                    "detail": _("Exercise not found or not accessible."),
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        cloned_exercise = Exercise.objects.create(
            t_start=original.t_start,
            t_break=original.t_break,
            repetition=original.repetition,
            distance=original.distance,
            notes=original.notes,
            modality=original.modality,
            energysegment=original.energysegment,
            language=round_obj.language,
            order=original.order,
        )
        round_obj.exercises.add(cloned_exercise)
        serializer = ExerciseSerializer(cloned_exercise, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
