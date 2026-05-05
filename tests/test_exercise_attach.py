"""POST /exercises/ with optional round_id (writeOnly) — atomic attach.

Same rationale as test_round_attach: the frontend posts and attaches in one
shot. Permission heuristic: at least one Event linked to the target Round
must belong to a team the user manages. Library rounds (no events) accept
the attach as-is — IsTrainer + (sport, language) scoping already cover the
catalog mutation case.
"""

import pytest

from event.models import Event
from program.models import Program
from round.models import Round
from tests.factories import (
    EnergySegmentFactory,
    EventFactory,
    ModalityFactory,
    ProgramFactory,
    RoundFactory,
    TeamFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


def test_POST_exercise_with_round_id_attaches_atomically(
    auth_client_trainer, trainer_user, trainer_sport
):
    """Manager of the round's event-team: exercise is created AND attached."""
    team = trainer_user.owned_teams.first()
    program = ProgramFactory(team=team)
    event = EventFactory(refer_program=program)
    round_obj = RoundFactory(sport=trainer_sport, language=team.language, event=event)
    modality = ModalityFactory(sport=trainer_sport)
    seg = EnergySegmentFactory()

    response = auth_client_trainer.post(
        "/api/v1/exercises/",
        {
            "modality_id": modality.pk,
            "energysegment_id": seg.pk,
            "language": team.language,
            "order": 1,
            "repetition": 1,
            "distance": 100,
            "round_id": round_obj.pk,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    body = response.json()
    new_exercise_id = body["id"]
    assert "round_id" not in body
    round_obj.refresh_from_db()
    assert round_obj.exercises.filter(pk=new_exercise_id).exists()


def test_POST_exercise_without_round_id_creates_library_exercise(
    auth_client_trainer, trainer_sport
):
    """Backward-compatible path: no round_id → library exercise."""
    modality = ModalityFactory(sport=trainer_sport)
    seg = EnergySegmentFactory()

    response = auth_client_trainer.post(
        "/api/v1/exercises/",
        {
            "modality_id": modality.pk,
            "energysegment_id": seg.pk,
            "language": "fr",
            "order": 1,
            "repetition": 1,
            "distance": 100,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    new_exercise_id = response.json()["id"]
    assert not Round.objects.filter(exercises__pk=new_exercise_id).exists()


def test_POST_exercise_with_round_id_non_manager_returns_403(auth_client_trainer, trainer_sport):
    """Round attached to an event of an unmanaged team → 403, no orphan."""
    other_owner = UserFactory()
    other_team = TeamFactory(owner=other_owner, sport=trainer_sport, is_active=True)
    other_program = ProgramFactory(team=other_team)
    other_event = EventFactory(refer_program=other_program)
    foreign_round = RoundFactory(sport=trainer_sport, language="fr", event=other_event)
    modality = ModalityFactory(sport=trainer_sport)
    seg = EnergySegmentFactory()

    response = auth_client_trainer.post(
        "/api/v1/exercises/",
        {
            "modality_id": modality.pk,
            "energysegment_id": seg.pk,
            "language": "fr",
            "order": 1,
            "repetition": 1,
            "distance": 100,
            "round_id": foreign_round.pk,
        },
        format="json",
    )
    assert response.status_code == 403, response.json()
    assert response.json()["code"] == "not_authorized_round"
    foreign_round.refresh_from_db()
    assert foreign_round.exercises.count() == 0


def test_POST_exercise_with_round_id_library_round_succeeds(auth_client_trainer, trainer_sport):
    """Library round (no events linked) → attach accepted; IsTrainer + catalog
    scoping cover the protection here."""
    library_round = RoundFactory(sport=trainer_sport, language="fr")
    assert library_round.event_set.count() == 0
    modality = ModalityFactory(sport=trainer_sport)
    seg = EnergySegmentFactory()

    response = auth_client_trainer.post(
        "/api/v1/exercises/",
        {
            "modality_id": modality.pk,
            "energysegment_id": seg.pk,
            "language": "fr",
            "order": 1,
            "repetition": 1,
            "distance": 100,
            "round_id": library_round.pk,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    new_exercise_id = response.json()["id"]
    library_round.refresh_from_db()
    assert library_round.exercises.filter(pk=new_exercise_id).exists()


def test_POST_exercise_with_round_id_as_team_manager_succeeds(api_client, trainer_sport):
    """Manager (not owner) of the round's event-team can attach."""
    owner = UserFactory()
    manager = UserFactory()
    team = TeamFactory(owner=owner, sport=trainer_sport, language="fr", is_active=True)
    team.managers.add(manager)
    program = Program.objects.create(name="P", team=team)
    event = Event.objects.create(name="E", refer_program=program)
    round_obj = RoundFactory(sport=trainer_sport, language="fr", event=event)
    modality = ModalityFactory(sport=trainer_sport)
    seg = EnergySegmentFactory()

    api_client.force_authenticate(user=manager)
    response = api_client.post(
        "/api/v1/exercises/",
        {
            "modality_id": modality.pk,
            "energysegment_id": seg.pk,
            "language": "fr",
            "order": 1,
            "repetition": 1,
            "distance": 100,
            "round_id": round_obj.pk,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    new_exercise_id = response.json()["id"]
    round_obj.refresh_from_db()
    assert round_obj.exercises.filter(pk=new_exercise_id).exists()
