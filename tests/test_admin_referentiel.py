"""CRUD admin tests for the catalog referential
(Sport, Modality, EnergySystem, EnergySegment).

Permission model :
  - Read  (SAFE_METHODS)  : any authenticated user.
  - Write (POST/PATCH/PUT/DELETE) : staff only.
  - DELETE soft-deletes (is_active = False).
  - Default queryset hides is_active=False.
  - ?include_inactive=true returns inactive items, only for staff.
  - Admin flavor of serializer (per-language name variants) is used
    for create/update/partial_update/retrieve when the requester is staff.
"""

import pytest

from tests.factories import (
    EnergySegmentFactory,
    EnergySystemFactory,
    ModalityFactory,
    SportFactory,
)

pytestmark = pytest.mark.django_db


# =====================================================================
# SPORT
# =====================================================================


# ---------- Permissions ----------------------------------------------


def test_GET_sports_as_authenticated_returns_200(auth_client):
    SportFactory()
    response = auth_client.get("/api/v1/sports/")
    assert response.status_code == 200


def test_POST_sport_as_non_staff_returns_403(auth_client):
    response = auth_client.post(
        "/api/v1/sports/",
        {"name_fr": "Course", "slug": "course-test", "is_active": True},
        format="json",
    )
    assert response.status_code == 403


def test_POST_sport_as_staff_returns_201(admin_client):
    response = admin_client.post(
        "/api/v1/sports/",
        {
            "name_fr": "Course à pied",
            "name_en": "Running",
            "slug": "running-test",
            "is_active": True,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["name_fr"] == "Course à pied"
    assert body["name_en"] == "Running"
    assert body["slug"] == "running-test"


def test_PATCH_sport_as_non_staff_returns_403(auth_client):
    sport = SportFactory(slug="patch-non-staff")
    response = auth_client.patch(
        f"/api/v1/sports/{sport.pk}/",
        {"slug": "patched"},
        format="json",
    )
    assert response.status_code == 403


def test_PATCH_sport_as_staff_returns_200(admin_client):
    sport = SportFactory(slug="patch-staff")
    response = admin_client.patch(
        f"/api/v1/sports/{sport.pk}/",
        {"name_nl": "Hardlopen"},
        format="json",
    )
    assert response.status_code == 200
    sport.refresh_from_db()
    assert sport.name_nl == "Hardlopen"


def test_DELETE_sport_as_non_staff_returns_403(auth_client):
    sport = SportFactory(slug="del-non-staff")
    response = auth_client.delete(f"/api/v1/sports/{sport.pk}/")
    assert response.status_code == 403


# ---------- Soft delete ----------------------------------------------


def test_DELETE_sport_as_staff_soft_deletes(admin_client):
    sport = SportFactory(slug="del-staff", is_active=True)
    response = admin_client.delete(f"/api/v1/sports/{sport.pk}/")
    assert response.status_code == 204
    sport.refresh_from_db()
    assert sport.is_active is False


def test_GET_sports_default_excludes_inactive(auth_client):
    SportFactory(slug="inactive-default", is_active=False)
    SportFactory(slug="active-default", is_active=True)
    response = auth_client.get("/api/v1/sports/")
    slugs = {s["slug"] for s in response.json()["results"]}
    assert "active-default" in slugs
    assert "inactive-default" not in slugs


def test_GET_sports_include_inactive_as_staff_returns_inactive(admin_client):
    SportFactory(slug="inactive-staff-view", is_active=False)
    response = admin_client.get("/api/v1/sports/?include_inactive=true")
    slugs = {s["slug"] for s in response.json()["results"]}
    assert "inactive-staff-view" in slugs


def test_GET_sports_include_inactive_as_non_staff_ignores_param(auth_client):
    SportFactory(slug="inactive-nonstaff-view", is_active=False)
    response = auth_client.get("/api/v1/sports/?include_inactive=true")
    slugs = {s["slug"] for s in response.json()["results"]}
    assert "inactive-nonstaff-view" not in slugs


# ---------- Serializer flavors ---------------------------------------


def test_GET_sport_as_admin_returns_admin_serializer_with_name_variants(admin_client):
    sport = SportFactory(slug="flavor-admin")
    sport.name_en = "Diving"
    sport.save()
    response = admin_client.get(f"/api/v1/sports/{sport.pk}/")
    body = response.json()
    assert "name_fr" in body
    assert "name_en" in body
    assert body["name_en"] == "Diving"


def test_GET_sport_as_non_staff_returns_public_serializer_no_variants(auth_client):
    sport = SportFactory(slug="flavor-public")
    response = auth_client.get(f"/api/v1/sports/{sport.pk}/")
    body = response.json()
    assert "name" in body
    assert "name_fr" not in body
    assert "name_en" not in body


# ---------- M2M Sport.energy_systems ---------------------------------


def test_POST_sport_with_energy_systems_creates_m2m(admin_client):
    es1 = EnergySystemFactory()
    es2 = EnergySystemFactory()
    response = admin_client.post(
        "/api/v1/sports/",
        {
            "name_fr": "Cyclisme test",
            "slug": "cyclisme-m2m-create",
            "is_active": True,
            "energy_systems": [es1.pk, es2.pk],
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    body = response.json()
    assert set(body["energy_systems"]) == {es1.pk, es2.pk}


def test_PATCH_sport_can_update_energy_systems(admin_client):
    sport = SportFactory(slug="m2m-patch")
    es = EnergySystemFactory()
    response = admin_client.patch(
        f"/api/v1/sports/{sport.pk}/",
        {"energy_systems": [es.pk]},
        format="json",
    )
    assert response.status_code == 200
    sport.refresh_from_db()
    assert list(sport.energy_systems.values_list("pk", flat=True)) == [es.pk]


# =====================================================================
# MODALITY
# =====================================================================


def test_POST_modality_as_non_staff_returns_403(auth_client):
    sport = SportFactory(slug="mod-non-staff")
    response = auth_client.post(
        "/api/v1/sports/{}/modalities/".format(sport.pk),
        {"name_fr": "Crawl test", "sport": sport.pk},
        format="json",
    )
    assert response.status_code == 403


def test_POST_modality_as_staff_returns_201(admin_client):
    sport = SportFactory(slug="mod-staff")
    response = admin_client.post(
        f"/api/v1/sports/{sport.pk}/modalities/",
        {"name_fr": "Crawl staff", "sport": sport.pk},
        format="json",
    )
    assert response.status_code == 201, response.json()


def test_DELETE_modality_as_staff_soft_deletes(admin_client):
    sport = SportFactory(slug="mod-soft-del")
    modality = ModalityFactory(sport=sport)
    response = admin_client.delete(f"/api/v1/sports/{sport.pk}/modalities/{modality.pk}/")
    assert response.status_code == 204
    modality.refresh_from_db()
    assert modality.is_active is False


# =====================================================================
# ENERGY SYSTEM
# =====================================================================


def test_POST_energysystem_as_staff_returns_201(admin_client):
    response = admin_client.post(
        "/api/v1/energy-systems/",
        {"name_fr": "Glycolyse", "is_active": True},
        format="json",
    )
    assert response.status_code == 201, response.json()
    assert response.json()["name_fr"] == "Glycolyse"


def test_DELETE_energysystem_as_staff_soft_deletes(admin_client):
    es = EnergySystemFactory()
    response = admin_client.delete(f"/api/v1/energy-systems/{es.pk}/")
    assert response.status_code == 204
    es.refresh_from_db()
    assert es.is_active is False


# =====================================================================
# ENERGY SEGMENT
# =====================================================================


def test_POST_energysegment_with_invalid_energysystem_returns_400(admin_client):
    response = admin_client.post(
        "/api/v1/energy-segments/",
        {
            "abv": "ZX",
            "description_fr": "test",
            "energy_system_id": 999999,
            "is_active": True,
        },
        format="json",
    )
    assert response.status_code == 400


def test_POST_energysegment_with_valid_energysystem_returns_201(admin_client):
    es = EnergySystemFactory()
    response = admin_client.post(
        "/api/v1/energy-segments/",
        {
            "abv": "ZTEST",
            "description_fr": "Test segment",
            "energy_system_id": es.pk,
            "is_active": True,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["abv"] == "ZTEST"
    assert body["description_fr"] == "Test segment"


def test_DELETE_energysegment_as_staff_soft_deletes(admin_client):
    seg = EnergySegmentFactory()
    response = admin_client.delete(f"/api/v1/energy-segments/{seg.pk}/")
    assert response.status_code == 204
    seg.refresh_from_db()
    assert seg.is_active is False
