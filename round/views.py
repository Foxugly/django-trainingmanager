from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from exercise.models import Exercise
from exercise.serializers import ExerciseSerializer
from team.permissions import IsTrainer
from team.utils import scope_by_sport_language

from .models import Round
from .serializers import ReorderExercisesRequestSerializer, RoundSerializer


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

    @extend_schema(
        request=ReorderExercisesRequestSerializer,
        responses={
            204: OpenApiResponse(description="Exercises reordered"),
            400: OpenApiResponse(
                description=(
                    "Validation error. `body.code` is one of: `empty_list`, "
                    "`duplicate_id`, `scope_mismatch`, `incomplete_reorder`."
                )
            ),
            403: OpenApiResponse(description="Not authorized to mutate this round"),
        },
        description=(
            "Atomically reorder the Exercises attached to this Round. "
            "`exercise_ids` must contain exactly the IDs of the Exercises "
            "currently attached, in the desired final order. Exercise.order "
            "is set to 1..N matching list position, in a single transaction."
        ),
    )
    @action(detail=True, methods=["post"], url_path="exercises/reorder")
    def exercises_reorder(self, request, pk=None):
        round_obj = self.get_object()
        if not _user_may_mutate_round(round_obj, request.user):
            return Response(
                {
                    "code": "not_authorized_round",
                    "detail": _(
                        "You must manage at least one team owning an event "
                        "linked to this round to reorder its exercises."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        body_serializer = ReorderExercisesRequestSerializer(data=request.data)
        body_serializer.is_valid(raise_exception=True)
        exercise_ids = body_serializer.validated_data["exercise_ids"]

        if not exercise_ids:
            raise ValidationError(
                detail={"detail": _("exercise_ids cannot be empty.")},
                code="empty_list",
            )
        if len(exercise_ids) != len(set(exercise_ids)):
            raise ValidationError(
                detail={"detail": _("exercise_ids contains duplicate IDs.")},
                code="duplicate_id",
            )

        expected_ids = set(round_obj.exercises.values_list("id", flat=True))
        submitted_ids = set(exercise_ids)
        if not submitted_ids.issubset(expected_ids):
            raise ValidationError(
                detail={
                    "detail": _(
                        "exercise_ids contains IDs not attached to this round: {ids}"
                    ).format(ids=sorted(submitted_ids - expected_ids)),
                },
                code="scope_mismatch",
            )
        if submitted_ids != expected_ids:
            raise ValidationError(
                detail={
                    "detail": _(
                        "exercise_ids is missing exercises attached to this round: {ids}"
                    ).format(ids=sorted(expected_ids - submitted_ids)),
                },
                code="incomplete_reorder",
            )

        with transaction.atomic():
            for index, exercise_id in enumerate(exercise_ids, start=1):
                Exercise.objects.filter(pk=exercise_id).update(order=index)

        return Response(status=status.HTTP_204_NO_CONTENT)


def _user_may_mutate_round(round_obj, user):
    """A user may reorder a round's exercises if they manage at least one
    team owning an event that contains this round. Library rounds (no
    events) fall back to the IsTrainer class permission check (already
    enforced by RoundViewSet.permission_classes)."""
    linked_events = list(round_obj.event_set.all())
    if not linked_events:
        return True  # library round; class-level IsTrainer already passed
    return any(
        e.refer_program is not None and e.refer_program.team.is_managed_by(user)
        for e in linked_events
    )
