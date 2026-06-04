from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from agenda.models import Agenda
from event.models import Event
from exercise.models import Exercise
from member.models import Member
from round.forms import RoundExerciseFormSet
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


class CrudTests(TestCase):
    """Full-page CRUD replaced the old (Django-6-broken) Bootstrap modals.

    These guard the create/update/delete POST → redirect → DB-effect path so the
    plumbing can't silently rot again.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="u", email="u@example.com", password="pw")
        self.client.login(username="u", password="pw")

    def test_member_create(self):
        r = self.client.post(reverse("member:member_add"),
                             {"firstname": "John", "lastname": "Doe", "phonenumber": "", "email": ""},
                             secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Member.objects.filter(firstname="John", lastname="Doe").exists())

    def test_member_create_enrols_in_event_agenda(self):
        agenda = Agenda.objects.create(name="A")
        event = Event.objects.create(name="E", refer_agenda=agenda)
        url = "%s?next=/&event_id=%d" % (reverse("member:member_add"), event.id)
        r = self.client.post(url, {"firstname": "Jane", "lastname": "Roe", "phonenumber": "", "email": ""},
                             secure=True)
        self.assertEqual(r.status_code, 302)
        m = Member.objects.get(firstname="Jane")
        self.assertIn(m, agenda.members.all())

    def test_member_update(self):
        m = Member.objects.create(firstname="Old", lastname="Name")
        r = self.client.post(reverse("member:member_change", kwargs={"pk": m.pk}),
                             {"firstname": "New", "lastname": "Name", "phonenumber": "", "email": ""},
                             secure=True)
        self.assertEqual(r.status_code, 302)
        m.refresh_from_db()
        self.assertEqual(m.firstname, "New")

    def test_member_delete(self):
        m = Member.objects.create(firstname="Gone", lastname="Soon")
        r = self.client.post(reverse("member:member_delete", kwargs={"pk": m.pk}), secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Member.objects.filter(pk=m.pk).exists())

    def test_event_create(self):
        r = self.client.post(reverse("event:event_add"),
                             {"name": "Friday", "goal": "", "color": "", "date": "", "hour_start": "", "hour_end": ""},
                             secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Event.objects.filter(name="Friday").exists())

    def test_round_create_with_empty_formset(self):
        agenda = Agenda.objects.create(name="A")
        event = Event.objects.create(name="E", refer_agenda=agenda)
        prefix = RoundExerciseFormSet().prefix
        data = {
            "order": 1, "count": 1, "t_start": "", "t_break": "", "refer_event": event.pk,
            "%s-TOTAL_FORMS" % prefix: 0, "%s-INITIAL_FORMS" % prefix: 0,
            "%s-MIN_NUM_FORMS" % prefix: 0, "%s-MAX_NUM_FORMS" % prefix: 1000,
        }
        r = self.client.post("%s?next=/" % reverse("round:round_add"), data, secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Round.objects.filter(refer_event=event).exists())
