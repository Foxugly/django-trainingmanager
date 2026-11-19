"""Regression tests for the 2026-11 security audit (TM-1 .. TM-9)."""
import datetime
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from agenda.models import Agenda
from event.models import Event
from event.views import PDF_CMD_OPTIONS
from exercise.models import Exercise, Stroke
from round.models import Round
from tools.generic_views import safe_next_url

User = get_user_model()

PAYLOAD = '<iframe src="file:///run/x/.env"></iframe><script>alert(1)</script>'


class EventFixtureMixin:
    def setUp(self):
        self.user = User.objects.create_user(username="u", email="u@example.com", password="pw")
        self.agenda = Agenda.objects.create(name="<b>agenda</b>")
        self.event = Event.objects.create(
            name="E", refer_agenda=self.agenda,
            date=datetime.date(2026, 1, 2), hour_start=datetime.time(18, 0),
        )
        self.round = Round.objects.create(order=1, count=1, t_break="<svg/x>", refer_event=self.event)
        stroke = Stroke.objects.create(name="<i>crawl</i>")
        self.exercise = Exercise.objects.create(order=1, distance=100, stroke=stroke, notes=PAYLOAD,
                                                refer_round=self.round)
        self.round.exercises.add(self.exercise)


class AnonymousAccessTests(EventFixtureMixin, TestCase):
    """TM-3 / TM-4: no view may act for an anonymous visitor."""

    def test_round_delete_requires_login(self):
        self.client.get("/accounts/login/", secure=True)  # obtain a CSRF cookie, like the exploit
        r = self.client.post(f"/round/round/{self.round.pk}/delete", secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/accounts/login/", r.url)
        self.assertTrue(Round.objects.filter(pk=self.round.pk).exists())

    def test_round_delete_unknown_pk_redirects_instead_of_404(self):
        r = self.client.get("/round/round/999999999/delete", secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/accounts/login/", r.url)

    def test_pdf_requires_login(self):
        with mock.patch("wkhtmltopdf.views.render_pdf_from_template") as render:
            r = self.client.get(f"/event/event/{self.event.pk}/pdf/", secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/accounts/login/", r.url)
        render.assert_not_called()

    def test_every_url_is_protected_by_default(self):
        # LoginRequiredMiddleware: even a view without LoginRequiredMixin redirects.
        for url in (f"/round/round/{self.round.pk}/", f"/exercise/exercise/{self.exercise.pk}/",
                    "/member/member/", f"/agenda/agenda/{self.agenda.pk}/", "/accounts/update/"):
            r = self.client.get(url, secure=True)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn("/accounts/login/", r.url, url)

    def test_public_endpoints_stay_public(self):
        self.assertEqual(self.client.get("/health/", secure=True).status_code, 200)
        self.assertEqual(self.client.get("/accounts/login/", secure=True).status_code, 200)
        self.assertEqual(self.client.get("/accounts/password_reset/", secure=True).status_code, 200)
        self.assertEqual(self.client.get("/admin/login/", secure=True).status_code, 200)
        r = self.client.get("/lang/?lang=fr&next=/accounts/login/", secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, "/accounts/login/")


class HtmlEscapingTests(EventFixtureMixin, TestCase):
    """TM-1 / TM-2: user text never reaches the page or the PDF as markup."""

    def assert_escaped(self, html):
        self.assertNotIn("<script>alert(1)", html)
        self.assertNotIn("<iframe", html)
        self.assertNotIn("<svg/x>", html)
        self.assertNotIn("<i>crawl</i>", html)
        self.assertNotIn("<b>agenda</b>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)

    def test_model_builders_escape(self):
        self.assert_escaped(str(self.event.get_table()))
        self.assert_escaped(str(self.event.get_table_raw()))
        self.assertIn("&lt;b&gt;agenda&lt;/b&gt;", str(self.event.get_title_raw()))

    def test_event_page_escapes(self):
        self.client.login(username="u", password="pw")
        r = self.client.get(f"/event/event/{self.event.pk}/", secure=True)
        self.assertEqual(r.status_code, 200)
        self.assert_escaped(r.content.decode())

    def test_event_raw_page_escapes(self):
        self.client.login(username="u", password="pw")
        r = self.client.get(f"/event/event/{self.event.pk}/raw/", secure=True)
        self.assertEqual(r.status_code, 200)
        self.assert_escaped(r.content.decode())

    def test_pdf_html_escaped_and_no_local_file_access(self):
        captured = {}

        def fake_render(input_template, header_template, footer_template, context, request=None,
                        cmd_options=None, cover_template=None):
            captured["html"] = input_template.render(context, request)
            captured["cmd_options"] = cmd_options
            return b"%PDF-fake"

        self.client.login(username="u", password="pw")
        with mock.patch("wkhtmltopdf.views.render_pdf_from_template", side_effect=fake_render):
            r = self.client.get(f"/event/event/{self.event.pk}/pdf/", secure=True)
            r.render()
        self.assertEqual(r.status_code, 200)
        self.assert_escaped(captured["html"])
        self.assertNotIn('src="file://', captured["html"])  # the logo no longer comes from disk
        self.assertIn("data:image/jpeg;base64,", captured["html"])
        opts = captured["cmd_options"]
        self.assertNotIn("enable-local-file-access", opts)
        self.assertTrue(opts.get("disable-local-file-access"))
        self.assertTrue(opts.get("disable-javascript"))

    def test_global_wkhtmltopdf_options(self):
        for opts in (settings.WKHTMLTOPDF_CMD_OPTIONS, PDF_CMD_OPTIONS):
            self.assertNotIn("enable-local-file-access", opts)
            self.assertTrue(opts.get("disable-local-file-access"))
            self.assertTrue(opts.get("disable-javascript"))


class ProfileFormTests(TestCase):
    """TM-5: the self-service profile form cannot grant privileges."""

    def test_is_superuser_ignored(self):
        user = User.objects.create_user(username="u", email="u@example.com", password="pw")
        self.client.login(username="u", password="pw")
        r = self.client.post("/accounts/update/", {
            "username": "u", "email": "u@example.com", "language": "fr",
            "is_superuser": "on", "is_foo_admin": "on", "is_staff": "on",
        }, secure=True)
        self.assertEqual(r.status_code, 302)
        user.refresh_from_db()
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_foo_admin)


class OpenRedirectTests(TestCase):
    """TM-8: `next` must stay on this site."""

    def test_set_lang_refuses_external_next(self):
        for evil in ("https://example.org/", "//example.org/", "http://testserver/"):
            r = self.client.get("/lang/", {"lang": "fr", "next": evil}, secure=True)
            self.assertEqual(r.status_code, 302, evil)
            self.assertEqual(r.url, "/", evil)

    def test_set_lang_without_lang_no_longer_500(self):
        r = self.client.get("/lang/", secure=True)
        self.assertEqual(r.status_code, 302)

    def test_safe_next_url(self):
        rf = RequestFactory()
        self.assertEqual(safe_next_url(rf.get("/x", {"next": "https://example.org/"}, secure=True), "/d"), "/d")
        self.assertEqual(safe_next_url(rf.get("/x", {"next": "/event/event/1/"}, secure=True), "/d"),
                         "/event/event/1/")
        self.assertEqual(safe_next_url(rf.get("/x", secure=True), "/d"), "/d")

    def test_modal_success_url_refuses_external_next(self):
        User.objects.create_user(username="u", email="u@example.com", password="pw")
        self.client.login(username="u", password="pw")
        r = self.client.post("/member/member/add/?next=https://example.org/",
                             {"firstname": "A", "lastname": "B"}, secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(urlsplit(r.url).netloc, "")  # stays on this site (relative URL)


class SettingsHardeningTests(TestCase):
    """TM-9 / NET-4."""

    def test_missing_secret_key_fails_outside_debug(self):
        env = {k: v for k, v in os.environ.items() if k not in ("SECRET_KEY", "DEBUG")}
        env.update(SECRET_KEY="", DEBUG="False", DJANGO_SETTINGS_MODULE="config.settings")
        base = Path(settings.BASE_DIR)
        proc = subprocess.run(
            [sys.executable, "-c", "import django; django.setup()"],
            cwd=base, env=env, capture_output=True, text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("SECRET_KEY must be set", proc.stderr)

    def test_hsts_and_csp_headers(self):
        r = self.client.get("/accounts/login/", secure=True)
        if not settings.DEBUG:
            self.assertEqual(settings.SECURE_HSTS_SECONDS, 31536000)
            self.assertIn("max-age=31536000", r.headers.get("Strict-Transport-Security", ""))
        csp = r.headers.get("Content-Security-Policy", "")
        self.assertIn("object-src 'none'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
