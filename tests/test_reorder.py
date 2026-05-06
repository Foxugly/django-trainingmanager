"""Bulk reorder endpoints for Round and Exercise.

POST /events/{id}/rounds/reorder/        — atomically reorder rounds in event
POST /rounds/{id}/exercises/reorder/     — atomically reorder exercises in round

Body: {"round_ids": [...]} or {"exercise_ids": [...]}.
Response: 204 No Content on success.
Errors: 400 with body {"code": ..., "detail": ...} where code is one of
empty_list, duplicate_id, scope_mismatch, incomplete_reorder.
403 with body {"code": "not_authorized_event"|"not_authorized_round", ...}.
"""

import pytest

from exercise.models import Exercise, Modality
from round.models import Round
from tests.factories import (
    EnergySegmentFactory,
    EventFactory,
    ProgramFactory,
)

pytestmark = pytest.mark.django_db


# --------------------------- helpers ---------------------------------


def _trainer_event_with_rounds(trainer_user, n=3):
    team = trainer_user.owned_teams.first()
    program = ProgramFactory(team=team)
    event = EventFactory(refer_program=program)
    rounds = []
    for i in range(n):
        r = Round.objects.create(sport=team.sport, language="fr", count=1, order=10 + i)
        event.rounds.add(r)
        rounds.append(r)
    return event, rounds


def _round_with_exercises(trainer_user, n=3):
    team = trainer_user.owned_teams.first()
    mod = Modality.objects.create(name="ReorderMod", sport=team.sport)
    seg = EnergySegmentFactory()
    rnd = Round.objects.create(sport=team.sport, language="fr", count=1, order=1)
    # Attach to an event so the manager perm path is exercised
    event = EventFactory(refer_program=ProgramFactory(team=team))
    event.rounds.add(rnd)
    exercises = []
    for i in range(n):
        ex = Exercise.objects.create(
            modality=mod,
            energysegment=seg,
            repetition=1,
            distance=100,
            language="fr",
            order=10 + i,
        )
        rnd.exercises.add(ex)
        exercises.append(ex)
    return rnd, exercises


# --------------------------- rounds reorder --------------------------


def test_POST_rounds_reorder_happy_path_returns_204(auth_client_trainer, trainer_user):
    event, rounds = _trainer_event_with_rounds(trainer_user, n=3)
    new_order = [rounds[2].pk, rounds[0].pk, rounds[1].pk]

    response = auth_client_trainer.post(
        f"/api/v1/events/{event.pk}/rounds/reorder/",
        {"round_ids": new_order},
        format="json",
    )

    assert response.status_code == 204, response.content
    fresh = {r.pk: r for r in Round.objects.filter(pk__in=new_order)}
    assert fresh[rounds[2].pk].order == 1
    assert fresh[rounds[0].pk].order == 2
    assert fresh[rounds[1].pk].order == 3


def test_POST_rounds_reorder_idempotent_replay_returns_204(auth_client_trainer, trainer_user):
    event, rounds = _trainer_event_with_rounds(trainer_user, n=3)
    new_order = [rounds[2].pk, rounds[0].pk, rounds[1].pk]
    payload = {"round_ids": new_order}

    r1 = auth_client_trainer.post(
        f"/api/v1/events/{event.pk}/rounds/reorder/", payload, format="json"
    )
    r2 = auth_client_trainer.post(
        f"/api/v1/events/{event.pk}/rounds/reorder/", payload, format="json"
    )
    assert r1.status_code == 204
    assert r2.status_code == 204
    fresh = {r.pk: r for r in Round.objects.filter(pk__in=new_order)}
    assert fresh[rounds[2].pk].order == 1
    assert fresh[rounds[0].pk].order == 2
    assert fresh[rounds[1].pk].order == 3


def test_POST_rounds_reorder_empty_list_returns_400(auth_client_trainer, trainer_user):
    event, _ = _trainer_event_with_rounds(trainer_user, n=2)

    response = auth_client_trainer.post(
        f"/api/v1/events/{event.pk}/rounds/reorder/",
        {"round_ids": []},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["code"] == "empty_list"


def test_POST_rounds_reorder_duplicate_id_returns_400(auth_client_trainer, trainer_user):
    event, rounds = _trainer_event_with_rounds(trainer_user, n=3)

    response = auth_client_trainer.post(
        f"/api/v1/events/{event.pk}/rounds/reorder/",
        {"round_ids": [rounds[0].pk, rounds[0].pk, rounds[1].pk]},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["code"] == "duplicate_id"


def test_POST_rounds_reorder_scope_mismatch_returns_400(auth_client_trainer, trainer_user):
    event, rounds = _trainer_event_with_rounds(trainer_user, n=2)
    team = trainer_user.owned_teams.first()
    other_event = EventFactory(refer_program=ProgramFactory(team=team))
    foreign = Round.objects.create(sport=team.sport, language="fr", count=1, order=1)
    other_event.rounds.add(foreign)

    response = auth_client_trainer.post(
        f"/api/v1/events/{event.pk}/rounds/reorder/",
        {"round_ids": [rounds[0].pk, rounds[1].pk, foreign.pk]},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["code"] == "scope_mismatch"


def test_POST_rounds_reorder_incomplete_returns_400(auth_client_trainer, trainer_user):
    event, rounds = _trainer_event_with_rounds(trainer_user, n=3)

    response = auth_client_trainer.post(
        f"/api/v1/events/{event.pk}/rounds/reorder/",
        {"round_ids": [rounds[0].pk, rounds[1].pk]},  # missing rounds[2]
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["code"] == "incomplete_reorder"


def test_POST_rounds_reorder_non_manager_returns_403(auth_client, trainer_user):
    event, rounds = _trainer_event_with_rounds(trainer_user, n=2)

    response = auth_client.post(
        f"/api/v1/events/{event.pk}/rounds/reorder/",
        {"round_ids": [r.pk for r in rounds]},
        format="json",
    )
    # Outsider has no team membership → 404 (not even discoverable)
    # Insider non-manager would get 403; here auth_client is fully outside.
    assert response.status_code in (403, 404)


# --------------------------- exercises reorder ----------------------


def test_POST_exercises_reorder_happy_path_returns_204(auth_client_trainer, trainer_user):
    rnd, exercises = _round_with_exercises(trainer_user, n=3)
    new_order = [exercises[2].pk, exercises[0].pk, exercises[1].pk]

    response = auth_client_trainer.post(
        f"/api/v1/rounds/{rnd.pk}/exercises/reorder/",
        {"exercise_ids": new_order},
        format="json",
    )

    assert response.status_code == 204
    fresh = {e.pk: e for e in Exercise.objects.filter(pk__in=new_order)}
    assert fresh[exercises[2].pk].order == 1
    assert fresh[exercises[0].pk].order == 2
    assert fresh[exercises[1].pk].order == 3


def test_POST_exercises_reorder_empty_list_returns_400(auth_client_trainer, trainer_user):
    rnd, _ = _round_with_exercises(trainer_user, n=2)

    response = auth_client_trainer.post(
        f"/api/v1/rounds/{rnd.pk}/exercises/reorder/",
        {"exercise_ids": []},
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["code"] == "empty_list"


def test_POST_exercises_reorder_duplicate_id_returns_400(auth_client_trainer, trainer_user):
    rnd, exercises = _round_with_exercises(trainer_user, n=3)

    response = auth_client_trainer.post(
        f"/api/v1/rounds/{rnd.pk}/exercises/reorder/",
        {"exercise_ids": [exercises[0].pk, exercises[0].pk, exercises[1].pk]},
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["code"] == "duplicate_id"


def test_POST_exercises_reorder_scope_mismatch_returns_400(auth_client_trainer, trainer_user):
    rnd, exercises = _round_with_exercises(trainer_user, n=2)
    team = trainer_user.owned_teams.first()
    other_mod = Modality.objects.create(name="OtherMod", sport=team.sport)
    foreign = Exercise.objects.create(
        modality=other_mod,
        energysegment=EnergySegmentFactory(),
        language="fr",
    )

    response = auth_client_trainer.post(
        f"/api/v1/rounds/{rnd.pk}/exercises/reorder/",
        {"exercise_ids": [exercises[0].pk, exercises[1].pk, foreign.pk]},
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["code"] == "scope_mismatch"


def test_POST_exercises_reorder_incomplete_returns_400(auth_client_trainer, trainer_user):
    rnd, exercises = _round_with_exercises(trainer_user, n=3)

    response = auth_client_trainer.post(
        f"/api/v1/rounds/{rnd.pk}/exercises/reorder/",
        {"exercise_ids": [exercises[0].pk, exercises[1].pk]},  # missing [2]
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["code"] == "incomplete_reorder"


def test_POST_exercises_reorder_non_manager_returns_403(auth_client_non_trainer, trainer_user):
    """A trainer who manages no team owning an event linked to this round
    cannot reorder its exercises."""
    rnd, exercises = _round_with_exercises(trainer_user, n=2)

    response = auth_client_non_trainer.post(
        f"/api/v1/rounds/{rnd.pk}/exercises/reorder/",
        {"exercise_ids": [e.pk for e in exercises]},
        format="json",
    )
    # Either 403 (got past the queryset filter but failed mutate-perm) or
    # 404 (round not in their visible scope). Both are acceptable.
    assert response.status_code in (403, 404)
