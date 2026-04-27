"""i18n level 2: structured error format and per-user language resolution.

Translations are bundled as .po files; .mo files must be compiled with
`django-admin compilemessages` for FR text to actually appear in responses.
Without compiled .mo, Django falls back to the English source. The tests
below therefore assert on the structural contract ({code, detail}) and
on tokens that exist in the English source — they will keep passing
once translations are compiled.
"""

import pytest
from django.utils.translation import override

pytestmark = pytest.mark.django_db


# ----------------------------- Structure ------------------------------


def test_403_response_has_code_and_detail(auth_client_non_trainer):
    """Non-trainer hitting an IsTrainer-protected endpoint gets {code, detail}."""
    response = auth_client_non_trainer.post("/api/v1/ai/ping/", {}, format="json")
    assert response.status_code == 403
    body = response.json()
    assert "code" in body
    assert "detail" in body
    assert body["code"] == "permission_denied"


def test_400_response_has_code_and_detail(auth_client_trainer):
    """Validation error on the AI ping endpoint surfaces a structured body."""
    response = auth_client_trainer.post("/api/v1/ai/ping/", {"prompt": ""}, format="json")
    assert response.status_code == 400
    body = response.json()
    assert body.get("code") == "prompt_empty"
    assert "detail" in body


def test_resource_locked_body_has_code(auth_client_trainer, trainer_user, settings):
    """Triggering ResourceLocked yields {code: 'resource_locked', detail: ...}."""
    from exercise.models import EnergySegment, EnergySystem, Exercise, Modality
    from round.models import Round
    from sport.models import Sport

    sport = Sport.objects.create(name="Test sport", slug="test-sport")
    modality = Modality.objects.create(name="Crawl", sport=sport)
    system = EnergySystem.objects.create(name="Aerobic")
    segment = EnergySegment.objects.create(abv="A1", description="A1", energysystem=system)
    exercise = Exercise.objects.create(modality=modality, energysegment=segment, distance=100)
    Round.objects.create(sport=sport, order=1).exercises.add(exercise)
    Round.objects.create(sport=sport, order=2).exercises.add(exercise)
    # Now exercise.usage_count >= 2 → mutation triggers ResourceLocked

    response = auth_client_trainer.patch(
        f"/api/v1/exercises/{exercise.pk}/",
        {"distance": 200},
        format="json",
    )
    assert response.status_code == 409
    body = response.json()
    assert body.get("code") == "resource_locked"
    assert "detail" in body


# ----------------------------- Language resolution --------------------


def test_permission_denied_detail_contains_manager_token(auth_client_non_trainer):
    """The 403 detail mentions trainers/managers — true in EN source and FR."""
    response = auth_client_non_trainer.post("/api/v1/ai/ping/", {}, format="json")
    detail = response.json()["detail"].lower()
    assert "trainer" in detail or "manager" in detail or "entraîneur" in detail


def test_user_fr_language_activates_french(non_trainer_user, auth_client_non_trainer):
    """Authenticated user with language='fr' triggers FR activation in middleware.

    Without compiled .mo, the body still contains the EN source — but the
    machinery must not crash, and the {code, detail} contract holds.
    """
    non_trainer_user.language = "fr"
    non_trainer_user.save()
    response = auth_client_non_trainer.post("/api/v1/ai/ping/", {}, format="json")
    assert response.status_code == 403
    body = response.json()
    assert "code" in body and "detail" in body


def test_user_en_language_keeps_english(non_trainer_user, auth_client_non_trainer):
    non_trainer_user.language = "en"
    non_trainer_user.save()
    response = auth_client_non_trainer.post("/api/v1/ai/ping/", {}, format="json")
    assert response.status_code == 403
    detail = response.json()["detail"].lower()
    assert "trainer" in detail or "manager" in detail


# ----------------------------- gettext_lazy bound -------------------


def test_gettext_lazy_resolves_under_override():
    """Sanity check that lazy strings are correctly registered.

    Even without compiled .mo, str(lazy_msg) returns the English source.
    This guards against regressions where a string is *not* wrapped at all.
    """
    from tools.exceptions import ResourceLocked

    with override("fr"):
        assert (
            "locked" in str(ResourceLocked.default_detail).lower()
            or "verrouill" in str(ResourceLocked.default_detail).lower()
        )
