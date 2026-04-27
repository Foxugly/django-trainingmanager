"""Phase 5 — catalog (Exercise, Round) is scoped by user's sports.

A user only sees exercises/rounds whose sport matches at least one of
their active teams' sports (owner, manager, or athlete role).
"""

import pytest

from tests.factories import (
    EnergySegmentFactory,
    ExerciseFactory,
    ModalityFactory,
    RoundFactory,
    SportFactory,
    TeamFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


def test_GET_exercises_only_returns_user_sport_exercises(api_client):
    natation = SportFactory(slug="natation-scoping", name="Natation Scoping")
    course = SportFactory(slug="course-scoping", name="Course Scoping")

    user = UserFactory()
    TeamFactory(owner=user, sport=natation, is_active=True)

    nat_modality = ModalityFactory(sport=natation)
    crs_modality = ModalityFactory(sport=course)
    seg = EnergySegmentFactory()

    nat_exercise = ExerciseFactory(modality=nat_modality, energysegment=seg)
    crs_exercise = ExerciseFactory(modality=crs_modality, energysegment=seg)

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/v1/exercises/")
    assert response.status_code == 200
    ids = {e["id"] for e in response.json()["results"]}
    assert nat_exercise.pk in ids
    assert crs_exercise.pk not in ids


def test_GET_rounds_only_returns_user_sport_rounds(api_client):
    natation = SportFactory(slug="natation-scoping-r", name="Natation R")
    course = SportFactory(slug="course-scoping-r", name="Course R")

    user = UserFactory()
    TeamFactory(owner=user, sport=natation, is_active=True)

    nat_round = RoundFactory(sport=natation)
    crs_round = RoundFactory(sport=course)

    api_client.force_authenticate(user=user)
    response = api_client.get("/api/v1/rounds/")
    assert response.status_code == 200
    ids = {r["id"] for r in response.json()["results"]}
    assert nat_round.pk in ids
    assert crs_round.pk not in ids


def test_GET_exercises_user_without_team_sees_nothing(api_client):
    """A user with no team membership must not see any exercise."""
    sport = SportFactory(slug="lonely-natation", name="Lonely")
    modality = ModalityFactory(sport=sport)
    seg = EnergySegmentFactory()
    ExerciseFactory(modality=modality, energysegment=seg)

    user = UserFactory()
    api_client.force_authenticate(user=user)
    response = api_client.get("/api/v1/exercises/")
    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_GET_rounds_user_without_team_sees_nothing(api_client):
    sport = SportFactory(slug="lonely-natation-r", name="Lonely R")
    RoundFactory(sport=sport)

    user = UserFactory()
    api_client.force_authenticate(user=user)
    response = api_client.get("/api/v1/rounds/")
    assert response.status_code == 200
    assert response.json()["count"] == 0
