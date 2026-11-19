"""The admin 2FA (admin_2fa/) changes /admin/ only, and fits LoginRequiredMiddleware.

- The site itself (/accounts/login/ then the app pages) still needs a password
  only, staff included, enrolled or not.
- The password-authenticated but not yet OTP-verified staff user must reach
  /admin/2fa/setup|verify/ (LoginRequiredMiddleware lets any authenticated user
  through; the 2FA views gate on staff themselves), and /admin/login/ stays public.
- Logging in through the site's own form never opens the admin.
"""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

from agenda.models import Agenda
from event.models import Event

User = get_user_model()
PASSWORD = "sup3rSecret!"


class Admin2FASiteTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="ops", email="ops@example.com", password=PASSWORD)
        self.staff.is_staff = True
        self.staff.save()
        agenda = Agenda.objects.create(name="A")
        self.event = Event.objects.create(
            name="E", refer_agenda=agenda, date=datetime.date(2026, 1, 2), hour_start=datetime.time(18, 0),
        )

    def _site_login(self):
        return self.client.post(
            "/accounts/login/", {"username": "ops", "password": PASSWORD}, secure=True
        )

    def _admin_login(self):
        return self.client.post(
            reverse("admin:login"), {"username": "ops", "password": PASSWORD, "next": "/admin/"}, secure=True
        )

    def test_staff_uses_the_site_with_a_password_only(self):
        for enrolled in (False, True):
            with self.subTest(enrolled=enrolled):
                TOTPDevice.objects.filter(user=self.staff).delete()
                if enrolled:
                    TOTPDevice.objects.create(user=self.staff, name="admin-2fa", confirmed=True)
                self.client.logout()
                self.assertEqual(self._site_login().status_code, 302)
                for url in ("/", "/agenda/agenda/", f"/event/event/{self.event.pk}/"):
                    self.assertEqual(self.client.get(url, secure=True).status_code, 200, url)

    def test_health_and_admin_login_stay_public(self):
        self.assertEqual(self.client.get("/health/", secure=True).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:login"), secure=True).status_code, 200)

    def test_password_authenticated_staff_reaches_the_enrolment_page(self):
        response = self._admin_login()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("admin:2fa_setup")))
        page = self.client.get(response.url, secure=True)
        self.assertEqual(page.status_code, 200)  # not bounced to /accounts/login/
        self.assertIn(b'aria-label="QR code"', page.content)

    def test_password_authenticated_enrolled_staff_reaches_the_verify_page(self):
        TOTPDevice.objects.create(user=self.staff, name="admin-2fa", confirmed=True)
        response = self._admin_login()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("admin:2fa_verify")))
        page = self.client.get(response.url, secure=True)
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'name="token"', page.content)

    def test_site_login_does_not_open_the_admin(self):
        self._site_login()
        response = self.client.get("/admin/", secure=True)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("admin:login")))
        # ... and the admin login forwards the half-logged-in staff to the second factor.
        follow = self.client.get(response.url, secure=True)
        self.assertEqual(follow.status_code, 302)
        self.assertTrue(follow.url.startswith(reverse("admin:2fa_setup")))
