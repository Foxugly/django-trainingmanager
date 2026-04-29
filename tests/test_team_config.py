"""Coverage of Team config toggles: chat_mode + athlete_can_read_notes.

Both fields are owner/manager-editable via PATCH /api/v1/teams/{id}/.
Fields surface on TeamSerializer (full); they are intentionally NOT
on TeamMinimalSerializer (kept lean for nested read contexts).
"""

import pytest

from tests.factories import TeamFactory

pytestmark = pytest.mark.django_db


# ----------------------------- defaults DB --------------------------


def test_team_default_chat_mode_is_all():
    team = TeamFactory()
    assert team.chat_mode == "all"


def test_team_default_athlete_can_read_notes_is_false():
    team = TeamFactory()
    assert team.athlete_can_read_notes is False


# ----------------------------- serializer exposure ------------------


def test_team_serializer_exposes_chat_mode_and_notes_flag(auth_client_trainer, trainer_user):
    team = trainer_user.owned_teams.first()
    response = auth_client_trainer.get(f"/api/v1/teams/{team.pk}/")
    assert response.status_code == 200
    body = response.json()
    assert "chat_mode" in body
    assert body["chat_mode"] == "all"
    assert "athlete_can_read_notes" in body
    assert body["athlete_can_read_notes"] is False


# ----------------------------- write permissions --------------------


def test_team_owner_can_patch_chat_mode(auth_client_trainer, trainer_user):
    team = trainer_user.owned_teams.first()
    response = auth_client_trainer.patch(
        f"/api/v1/teams/{team.pk}/",
        {"chat_mode": "coaches_only"},
        format="json",
    )
    assert response.status_code == 200
    team.refresh_from_db()
    assert team.chat_mode == "coaches_only"


def test_team_manager_can_patch_athlete_can_read_notes(
    api_client, trainer_user, authenticated_user
):
    team = trainer_user.owned_teams.first()
    team.managers.add(authenticated_user)
    api_client.force_authenticate(user=authenticated_user)
    response = api_client.patch(
        f"/api/v1/teams/{team.pk}/",
        {"athlete_can_read_notes": True},
        format="json",
    )
    assert response.status_code == 200
    team.refresh_from_db()
    assert team.athlete_can_read_notes is True


def test_team_random_user_cannot_patch_config(api_client, trainer_user, non_trainer_user):
    """A random authenticated user (neither owner nor manager) is
    blocked: 403 if the team is public/visible, 404 if private."""
    team = trainer_user.owned_teams.first()
    team.is_public = True
    team.save(update_fields=["is_public"])
    api_client.force_authenticate(user=non_trainer_user)
    response = api_client.patch(
        f"/api/v1/teams/{team.pk}/",
        {"chat_mode": "coaches_only"},
        format="json",
    )
    assert response.status_code == 403


# ----------------------------- validation ---------------------------


def test_team_invalid_chat_mode_returns_400(auth_client_trainer, trainer_user):
    team = trainer_user.owned_teams.first()
    response = auth_client_trainer.patch(
        f"/api/v1/teams/{team.pk}/",
        {"chat_mode": "invalid_mode"},
        format="json",
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert "chat_mode" in body.get("fields", {})
