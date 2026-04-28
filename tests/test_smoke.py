import pytest

from tests.factories import (
    EnergySegmentFactory,
    EnergySystemFactory,
    EventFactory,
    MemberFactory,
    ModalityFactory,
    ProgramFactory,
    SportFactory,
)

pytestmark = pytest.mark.django_db


# ------------------------------- /me/ --------------------------------


def test_GET_me_authenticated_returns_200(auth_client, authenticated_user):
    response = auth_client.get("/api/v1/me/")
    assert response.status_code == 200
    assert response.json()["username"] == authenticated_user.username


def test_PATCH_me_updates_first_name(auth_client):
    response = auth_client.patch("/api/v1/me/", {"first_name": "Updated"}, format="json")
    assert response.status_code == 200
    assert response.json()["first_name"] == "Updated"


def test_GET_me_unauthenticated_returns_401(api_client):
    response = api_client.get("/api/v1/me/")
    assert response.status_code == 401


# ------------------------------ /teams/ ------------------------------


def test_GET_teams_authenticated_returns_200(auth_client):
    response = auth_client.get("/api/v1/teams/")
    assert response.status_code == 200


def test_POST_teams_creates_with_caller_as_owner(auth_client, authenticated_user):
    sport = SportFactory()
    response = auth_client.post(
        "/api/v1/teams/",
        {
            "name": "New Team Smoke",
            "sport_id": sport.pk,
            "is_active": True,
            "is_public": False,
            "managers": [],
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["owner"]["id"] == authenticated_user.pk


def test_POST_teams_without_sport_returns_400(auth_client):
    response = auth_client.post(
        "/api/v1/teams/",
        {"name": "No sport", "is_active": True, "is_public": False, "managers": []},
        format="json",
    )
    assert response.status_code == 400


def test_GET_team_owner_is_nested_in_response(auth_client, user_team, authenticated_user):
    response = auth_client.get(f"/api/v1/teams/{user_team.pk}/")
    assert response.status_code == 200
    body = response.json()
    assert body["owner"]["id"] == authenticated_user.pk
    assert body["owner"]["username"] == authenticated_user.username
    assert isinstance(body["sport"], dict)
    assert body["sport"]["id"] == user_team.sport.pk


def test_GET_team_detail_returns_200(auth_client, user_team):
    response = auth_client.get(f"/api/v1/teams/{user_team.pk}/")
    assert response.status_code == 200
    assert response.json()["id"] == user_team.pk


# ----------------------------- /programs/ -----------------------------


def test_GET_programs_returns_200(auth_client):
    response = auth_client.get("/api/v1/programs/")
    assert response.status_code == 200


def test_POST_programs_with_owned_team_returns_201(auth_client, user_team):
    response = auth_client.post(
        "/api/v1/programs/",
        {"name": "Smoke Program", "team_id": user_team.pk},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["team"]["id"] == user_team.pk


def test_GET_program_detail_returns_200(auth_client, user_team):
    program = ProgramFactory(team=user_team)
    response = auth_client.get(f"/api/v1/programs/{program.pk}/")
    assert response.status_code == 200


def test_DELETE_program_returns_204(auth_client, user_team):
    program = ProgramFactory(team=user_team)
    response = auth_client.delete(f"/api/v1/programs/{program.pk}/")
    assert response.status_code == 204


# ------------------------------ /events/ -----------------------------


def test_GET_events_returns_200(auth_client):
    response = auth_client.get("/api/v1/events/")
    assert response.status_code == 200


def test_POST_events_with_valid_program_returns_201(auth_client, user_team):
    program = ProgramFactory(team=user_team)
    response = auth_client.post(
        "/api/v1/events/",
        {"name": "Smoke Event", "refer_program_id": program.pk},
        format="json",
    )
    assert response.status_code == 201


# ------------------------------ /rounds/ -----------------------------


def test_GET_rounds_returns_200(auth_client):
    response = auth_client.get("/api/v1/rounds/")
    assert response.status_code == 200


def test_POST_rounds_returns_201(auth_client_trainer):
    sport = SportFactory()
    response = auth_client_trainer.post(
        "/api/v1/rounds/",
        {"order": 1, "count": 1, "sport_id": sport.pk, "language": "fr"},
        format="json",
    )
    assert response.status_code == 201


# --------------------------- /exercises/ -----------------------------


def test_GET_exercises_returns_200(auth_client):
    response = auth_client.get("/api/v1/exercises/")
    assert response.status_code == 200


def test_POST_exercises_returns_201(auth_client_trainer):
    response = auth_client_trainer.post(
        "/api/v1/exercises/",
        {"order": 1, "repetition": 1, "distance": 100, "language": "fr"},
        format="json",
    )
    assert response.status_code == 201


# --------- /sports/, nested modalities/, energy-systems/, energy-segments/ (RO) ---------


def test_GET_sports_returns_200(auth_client):
    SportFactory()
    response = auth_client.get("/api/v1/sports/")
    assert response.status_code == 200


def test_GET_nested_modalities_returns_200(auth_client):
    sport = SportFactory()
    ModalityFactory(sport=sport)
    response = auth_client.get(f"/api/v1/sports/{sport.pk}/modalities/")
    assert response.status_code == 200


def test_POST_nested_modalities_as_non_staff_returns_403(auth_client):
    sport = SportFactory()
    response = auth_client.post(
        f"/api/v1/sports/{sport.pk}/modalities/", {"name": "Foo"}, format="json"
    )
    assert response.status_code == 403


def test_GET_energy_systems_returns_200(auth_client):
    EnergySystemFactory()
    response = auth_client.get("/api/v1/energy-systems/")
    assert response.status_code == 200


def test_GET_energy_segments_returns_200(auth_client):
    EnergySegmentFactory()
    response = auth_client.get("/api/v1/energy-segments/")
    assert response.status_code == 200


# ----------------------------- /members/ -----------------------------


def test_GET_members_returns_200(auth_client):
    response = auth_client.get("/api/v1/members/")
    assert response.status_code == 200


def test_POST_members_with_owned_team_returns_201(auth_client, user_team):
    response = auth_client.post(
        "/api/v1/members/",
        {
            "firstname": "Smoke",
            "lastname": "Tester",
            "email": "smoke.tester@local.test",
            "teams": [user_team.pk],
        },
        format="json",
    )
    assert response.status_code == 201


# ----------------------- schema and docs ----------------------------


def test_GET_schema_unauthenticated_returns_200(api_client):
    response = api_client.get("/api/v1/schema/")
    assert response.status_code == 200


def test_GET_docs_unauthenticated_returns_200(api_client):
    response = api_client.get("/api/v1/docs/")
    assert response.status_code == 200


# ------------------ filtering / search / ordering -------------------


def test_GET_programs_with_ordering_returns_200(auth_client, user_team):
    ProgramFactory.create_batch(3, team=user_team)
    response = auth_client.get("/api/v1/programs/?ordering=name")
    assert response.status_code == 200


def test_GET_members_with_search_returns_200(auth_client, user_team):
    MemberFactory(firstname="Searchable", teams=[user_team])
    response = auth_client.get("/api/v1/members/?search=Searchable")
    assert response.status_code == 200


def test_GET_events_filtered_by_refer_program_returns_200(auth_client, user_team):
    program = ProgramFactory(team=user_team)
    EventFactory(refer_program=program)
    response = auth_client.get(f"/api/v1/events/?refer_program={program.pk}")
    assert response.status_code == 200
