"""Each outbound email must be rendered in the recipient's language.

Recipient definition:
- Known user (has CustomUser.language): use user.language.
- Unknown email (e.g. trainer invite to a not-yet-registered athlete):
  fall back to team.language.

We assert the language *activation* via translation.override mocking,
because exercising the real .po catalogs in tests would couple them
to translation completeness — out of scope for this guard.
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from member.models import Member
from team.models import TeamInvitation
from tests.factories import TeamFactory, UserFactory

pytestmark = pytest.mark.django_db


User = get_user_model()


def test_join_request_notification_uses_each_recipient_language(api_client):
    """Owner = fr, manager = nl. Two distinct activate calls, one per
    recipient, with the recipient's user.language."""
    owner = UserFactory(
        email="owner_fr@local.test", language="fr", first_name="Own", last_name="Er"
    )
    mgr = UserFactory(email="mgr_nl@local.test", language="nl", first_name="Man", last_name="Ager")
    team = TeamFactory(owner=owner, is_active=True, is_public=True, language="en")
    team.managers.add(mgr)
    requester = UserFactory(language="en")
    api_client.force_authenticate(user=requester)

    with patch(
        "team.views.translation.override",
        wraps=__import__("django.utils.translation", fromlist=["override"]).override,
    ) as mock_override:
        response = api_client.post(
            "/api/v1/join-requests/",
            {"team": team.pk, "message": "hi"},
            format="json",
        )
    assert response.status_code == 201
    # The override was called twice (once per recipient) with the right lang.
    langs_used = [call.args[0] for call in mock_override.call_args_list]
    assert sorted(langs_used) == ["fr", "nl"]


def test_join_request_notification_falls_back_to_en_when_user_language_blank(api_client):
    """If a user has language="" (legacy data), fall back to en."""
    owner = UserFactory(email="owner_blank@local.test", language="")
    team = TeamFactory(owner=owner, is_active=True, is_public=True)
    requester = UserFactory()
    api_client.force_authenticate(user=requester)

    with patch(
        "team.views.translation.override",
        wraps=__import__("django.utils.translation", fromlist=["override"]).override,
    ) as mock_override:
        response = api_client.post(
            "/api/v1/join-requests/",
            {"team": team.pk},
            format="json",
        )
    assert response.status_code == 201
    langs_used = [call.args[0] for call in mock_override.call_args_list]
    assert langs_used == ["en"]


def test_invitation_email_uses_team_language(api_client):
    """The invitee has no user account yet → no user.language. Use team.language."""
    trainer = UserFactory(email="trainer@local.test", first_name="T", last_name="R", language="fr")
    team = TeamFactory(owner=trainer, is_active=True, language="nl")  # team in NL
    trainer.refresh_from_db()
    trainer.team_quota = 5
    trainer.save(update_fields=["team_quota"])
    api_client.force_authenticate(user=trainer)

    with patch(
        "team.views.translation.override",
        wraps=__import__("django.utils.translation", fromlist=["override"]).override,
    ) as mock_override:
        response = api_client.post(
            "/api/v1/invitations/",
            {
                "team": team.pk,
                "email": "newathlete@local.test",
                "firstname": "New",
                "lastname": "Athlete",
            },
            format="json",
        )
    assert response.status_code == 201
    # Should use team.language (nl), NOT trainer.language (fr).
    langs_used = [call.args[0] for call in mock_override.call_args_list]
    assert langs_used == ["nl"]
    # Sanity: an invitation row was created.
    assert TeamInvitation.objects.filter(email="newathlete@local.test").exists()
    # Member is created with the right email.
    assert Member.objects.filter(email="newathlete@local.test").exists()
