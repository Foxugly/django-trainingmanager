"""Validates t_start / t_break MM:SS regex on Round and Exercise.

Single shared validator (`tools.validators.MMSS_VALIDATOR`) wired on both
the model fields and the serializers — backend rejects any non-MM:SS
string the frontend would also reject, and the OpenAPI schema exposes
the regex as `pattern`.
"""

import pytest

from exercise.models import Exercise, Modality
from round.models import Round
from tests.factories import EnergySegmentFactory

pytestmark = pytest.mark.django_db


# ----------------------------- Round --------------------------------


def _trainer_round(trainer_user):
    team = trainer_user.owned_teams.first()
    return Round.objects.create(sport=team.sport, language="fr", count=1, order=1)


@pytest.mark.parametrize("value", ["0:30", "1:00", "45:30", "10:59", "999:00"])
def test_PATCH_round_t_start_valid_mmss_returns_200(auth_client_trainer, trainer_user, value):
    rnd = _trainer_round(trainer_user)
    response = auth_client_trainer.patch(
        f"/api/v1/rounds/{rnd.pk}/",
        {"t_start": value},
        format="json",
    )
    assert response.status_code == 200, response.json()
    assert response.json()["t_start"] == value


def test_PATCH_round_t_start_empty_string_returns_200(auth_client_trainer, trainer_user):
    rnd = _trainer_round(trainer_user)
    response = auth_client_trainer.patch(
        f"/api/v1/rounds/{rnd.pk}/",
        {"t_start": ""},
        format="json",
    )
    assert response.status_code == 200, response.json()


def test_PATCH_round_t_start_null_returns_200(auth_client_trainer, trainer_user):
    rnd = _trainer_round(trainer_user)
    response = auth_client_trainer.patch(
        f"/api/v1/rounds/{rnd.pk}/",
        {"t_start": None},
        format="json",
    )
    assert response.status_code == 200, response.json()


@pytest.mark.parametrize(
    "value",
    [
        "30s",  # not a MM:SS
        "1:60",  # seconds > 59
        "abc",  # garbage
        ":30",  # missing minutes
        "1:5",  # seconds must be 2 digits
        "1:30:00",  # extra :SS
        "12345:30",  # minutes > 3 digits
    ],
)
def test_PATCH_round_t_start_invalid_returns_400(auth_client_trainer, trainer_user, value):
    rnd = _trainer_round(trainer_user)
    response = auth_client_trainer.patch(
        f"/api/v1/rounds/{rnd.pk}/",
        {"t_start": value},
        format="json",
    )
    assert response.status_code == 400, response.json()
    body = response.json()
    field_errors = body.get("fields", {}).get("t_start", [])
    assert any(err.get("code") == "time_mmss_invalid" for err in field_errors), body


def test_PATCH_round_t_break_invalid_returns_400(auth_client_trainer, trainer_user):
    rnd = _trainer_round(trainer_user)
    response = auth_client_trainer.patch(
        f"/api/v1/rounds/{rnd.pk}/",
        {"t_break": "30s"},
        format="json",
    )
    assert response.status_code == 400
    body = response.json()
    field_errors = body.get("fields", {}).get("t_break", [])
    assert any(err.get("code") == "time_mmss_invalid" for err in field_errors), body


def test_POST_round_without_t_fields_returns_201(auth_client_trainer, trainer_user):
    """Omitting the optional fields keeps backwards-compat with older clients."""
    team = trainer_user.owned_teams.first()
    response = auth_client_trainer.post(
        "/api/v1/rounds/",
        {
            "sport_id": team.sport_id,
            "language": "fr",
            "order": 1,
            "count": 1,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()


# ----------------------------- Exercise -----------------------------


def _trainer_exercise(trainer_user):
    team = trainer_user.owned_teams.first()
    mod = Modality.objects.create(name="Test-MMSS", sport=team.sport)
    seg = EnergySegmentFactory()
    return Exercise.objects.create(
        modality=mod,
        energysegment=seg,
        repetition=1,
        distance=100,
        language="fr",
    )


def test_PATCH_exercise_t_start_invalid_returns_400(auth_client_trainer, trainer_user):
    ex = _trainer_exercise(trainer_user)
    response = auth_client_trainer.patch(
        f"/api/v1/exercises/{ex.pk}/",
        {"t_start": "1:60"},
        format="json",
    )
    assert response.status_code == 400, response.json()
    body = response.json()
    field_errors = body.get("fields", {}).get("t_start", [])
    assert any(err.get("code") == "time_mmss_invalid" for err in field_errors), body


def test_PATCH_exercise_t_start_valid_returns_200(auth_client_trainer, trainer_user):
    ex = _trainer_exercise(trainer_user)
    response = auth_client_trainer.patch(
        f"/api/v1/exercises/{ex.pk}/",
        {"t_start": "0:30"},
        format="json",
    )
    assert response.status_code == 200, response.json()
    assert response.json()["t_start"] == "0:30"


def test_PATCH_exercise_t_break_empty_returns_200(auth_client_trainer, trainer_user):
    ex = _trainer_exercise(trainer_user)
    response = auth_client_trainer.patch(
        f"/api/v1/exercises/{ex.pk}/",
        {"t_break": ""},
        format="json",
    )
    assert response.status_code == 200, response.json()
