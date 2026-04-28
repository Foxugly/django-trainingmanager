"""Validate the unified error response format produced by the
custom_exception_handler:

    {
        "code": "<top_level_code>",
        "detail": "<top_level_message>",
        "fields": {                        # optional, only on multi-field
            "<field>": [{"code": "...", "detail": "..."}],
        }
    }
"""

import pytest

from tests.factories import TeamFactory

pytestmark = pytest.mark.django_db


# ---------- ValidationError multi-fields (dict shape) ----------------


def test_validation_error_multifield_returns_fields_dict(auth_client_trainer, trainer_user):
    """POST /join-requests/ with an inactive team triggers a multi-field
    ValidationError on `team` -> response carries `fields`."""
    team = TeamFactory(owner=trainer_user, is_active=False, is_public=True)
    response = auth_client_trainer.post(
        "/api/v1/join-requests/",
        {"team": team.pk, "message": "hi"},
        format="json",
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert "detail" in body
    assert "fields" in body
    assert "team" in body["fields"]
    team_errors = body["fields"]["team"]
    assert isinstance(team_errors, list) and team_errors
    first = team_errors[0]
    assert "code" in first and "detail" in first


# ---------- APIException keeps simple {code, detail} (no fields) -----


def test_permission_denied_has_code_detail_no_fields(auth_client_non_trainer):
    response = auth_client_non_trainer.post("/api/v1/ai/ping/", {}, format="json")
    assert response.status_code == 403
    body = response.json()
    assert body["code"] == "permission_denied"
    assert "detail" in body
    assert "fields" not in body


def test_resource_locked_has_code_detail_no_fields(auth_client_trainer, trainer_sport):
    """Triggering ResourceLocked should yield {code: 'resource_locked', detail}."""
    from exercise.models import EnergySegment, EnergySystem, Exercise, Modality
    from round.models import Round

    modality = Modality.objects.create(name="Lock test", sport=trainer_sport)
    system = EnergySystem.objects.create(name="LockSystem")
    segment = EnergySegment.objects.create(abv="LX", description="x", energysystem=system)
    exercise = Exercise.objects.create(
        modality=modality, energysegment=segment, distance=50, language="fr"
    )
    Round.objects.create(sport=trainer_sport, language="fr", order=1).exercises.add(exercise)
    Round.objects.create(sport=trainer_sport, language="fr", order=2).exercises.add(exercise)

    response = auth_client_trainer.patch(
        f"/api/v1/exercises/{exercise.pk}/",
        {"distance": 200},
        format="json",
    )
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "resource_locked"
    assert "detail" in body
    assert "fields" not in body


# ---------- ValidationError simple (single message, no fields) -------


def test_validation_error_simple_returns_no_fields(auth_client_trainer):
    """A simple AI ping with empty prompt returns {code, detail} (no fields)."""
    response = auth_client_trainer.post("/api/v1/ai/ping/", {"prompt": ""}, format="json")
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "prompt_empty"
    assert "detail" in body
    assert "fields" not in body


# ---------- Field-level error codes are ErrorDetail-aware -------------


def test_validation_error_fields_carry_subcodes(auth_client_trainer):
    """The per-field error list carries {code, detail} entries; built-in
    DRF codes (e.g. 'required') propagate when present."""
    response = auth_client_trainer.post(
        "/api/v1/teams/",
        {"name": "Missing sport"},
        format="json",
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert "fields" in body
    # sport_id is required -> field error with code='required' from DRF
    field_errors = body["fields"].get("sport_id") or body["fields"].get("sport")
    assert field_errors and "code" in field_errors[0] and "detail" in field_errors[0]


# ---------- Throttled (DRF builtin APIException) ---------------------


def test_throttled_response_keeps_code_detail(auth_client_trainer, settings):
    """Throttled (429) is an APIException with default_code='throttled'.
    It should carry {code, detail}, not {fields}."""
    settings.ANTHROPIC_API_KEY = ""
    from django.core.cache import cache

    cache.clear()
    last = None
    for _ in range(35):
        last = auth_client_trainer.post("/api/v1/ai/ping/", {"prompt": "hi"}, format="json")
        if last.status_code == 429:
            break
    assert last is not None and last.status_code == 429
    body = last.json()
    assert body["code"] == "throttled"
    assert "detail" in body
    assert "fields" not in body
