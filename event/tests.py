from django.contrib.auth import get_user_model
from django.test import TestCase

from agenda.models import Agenda
from event.models import Event
from exercise.models import Exercise
from member.models import Member
from round.models import Round

User = get_user_model()


class SmokeTests(TestCase):
    """Cheap regression guards for the site's public/critical endpoints."""

    def test_health(self):
        r = self.client.get("/health/", secure=True)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")
        self.assertEqual(r.json()["db"], "ok")

    def test_login_page(self):
        self.assertEqual(self.client.get("/accounts/login/", secure=True).status_code, 200)

    def test_home_authenticated(self):
        User.objects.create_user(username="u", email="u@example.com", password="pw")
        self.client.login(username="u", password="pw")
        self.assertEqual(self.client.get("/", secure=True).status_code, 200)

    def test_protected_views_require_login(self):
        # home + the app views are login-only; anonymous is redirected to login.
        for url in ("/", "/event/event/", "/agenda/agenda/"):
            r = self.client.get(url, secure=True)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn("/accounts/login/", r.url, url)

    def test_set_lang_redirects(self):
        # Regression: set_lang() called check_for_language() without importing it
        # (NameError on every /lang/ hit) — see config/urls.py.
        r = self.client.get("/lang/?lang=fr&next=/", secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, "/")


class EventModelTests(TestCase):
    def setUp(self):
        self.agenda = Agenda.objects.create()
        self.m1 = Member.objects.create(firstname="A", lastname="A")
        self.m2 = Member.objects.create(firstname="B", lastname="B")
        self.m3 = Member.objects.create(firstname="C", lastname="C")
        self.agenda.members.add(self.m1, self.m2, self.m3)
        self.event = Event.objects.create(name="E1", refer_agenda=self.agenda)

    def test_attendance_counts(self):
        self.event.members.add(self.m1)
        self.assertEqual(self.event.get_nb_members_present(), 1)
        self.assertEqual(self.event.get_nb_all_members(), 3)

    def test_get_attendance_members(self):
        self.event.members.add(self.m1)
        rows = self.event.get_attendance_members()
        self.assertEqual(len(rows), 3)
        attendance = {row["member"].pk: row["attendance"] for row in rows}
        self.assertTrue(attendance[self.m1.pk])
        self.assertFalse(attendance[self.m2.pk])
        self.assertFalse(attendance[self.m3.pk])

    def test_get_total(self):
        r = Round.objects.create(order=1, count=2, refer_event=self.event)
        ex1 = Exercise.objects.create(order=1, repetition=2, distance=100)  # 200
        ex2 = Exercise.objects.create(order=2, repetition=1, distance=50)   # 50
        r.exercises.add(ex1, ex2)
        # round total = count(2) * (200 + 50) = 500 ; event total = sum(rounds) = 500
        self.assertEqual(r.get_total(), 500)
        self.assertEqual(self.event.get_total(), 500)
