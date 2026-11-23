"""Sentry configuration (config/sentry.py, sentry-sdk 3).

Unit tests on the callbacks, then a real sentry-sdk client with the production
options and a capturing transport, reading what would have been sent.
"""

import json
import logging
import warnings

import sentry_sdk
from django.core.exceptions import DisallowedHost
from django.test import SimpleTestCase
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.transport import Transport

from config.sentry import before_send, before_send_span, sentry_options
from config.sentry_scrub import FILTERED

SECRETS = ("hunter2", "abc123", "k3y", "Bearer xyz", "203.0.113.9")


def leaked(data, *secrets):
    text = json.dumps(data, default=str)
    return [s for s in secrets if s in text]


class OptionsTests(SimpleTestCase):
    def test_init_raises_no_warning_and_collects_no_more(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client = sentry_sdk.Client(dsn=None, default_integrations=False, **sentry_options())
        self.assertEqual([str(w.message) for w in caught], [])
        dc = client.options["data_collection"]
        self.assertIs(dc["user_info"], False)
        self.assertEqual(dc["cookies"], {"mode": "off"})
        self.assertEqual(dc["http_bodies"], [])
        self.assertIs(dc["queues"], False)
        self.assertIs(dc["database_query_data"], False)
        self.assertEqual(dc["mcp"], {"inputs": False, "outputs": False})
        self.assertEqual(dc["stack_frame_variables"], {"mode": "denylist"})
        self.assertIs(client.options["attach_stacktrace"], False)

    def test_integrations_and_response_headers(self):
        options = sentry_options()
        self.assertEqual(options["data_collection"]["http_headers"]["response"], {"mode": "off"})
        django, logs = options["integrations"]
        self.assertIsInstance(django, DjangoIntegration)
        self.assertIs(django.cache_spans, False)
        self.assertIsInstance(logs, LoggingIntegration)
        self.assertIsNone(logs._logs_handler)  # no Sentry Logs
        self.assertEqual(logs._event_handler.level, logging.ERROR)


class CallbackTests(SimpleTestCase):
    def test_before_send_masks_request_data_extra_and_local_vars(self):
        event = before_send({
            "request": {"data": {"password": "hunter2", "title": "ok"},
                        "headers": {"Authorization": "Bearer xyz", "Accept": "*/*"}},
            "extra": {"token": "abc123", "page": 3},
            "user": {"id": "7", "ip_address": "203.0.113.9"},
            "breadcrumbs": {"values": [{"data": {"api_key": "k3y", "n": 1}}]},
            "exception": {"values": [{"stacktrace": {"frames": [
                {"vars": {"password": "hunter2", "i": 2}}]}}]},
        }, {})
        self.assertEqual(leaked(event, *SECRETS), [])
        self.assertEqual(event["request"]["data"]["title"], "ok")
        self.assertEqual(event["request"]["headers"]["Accept"], "*/*")
        self.assertEqual(event["extra"]["page"], 3)
        self.assertEqual(event["exception"]["values"][0]["stacktrace"]["frames"][0]["vars"]["i"], 2)

    def test_before_send_drops_disallowed_host(self):
        self.assertIsNone(before_send({}, {"exc_info": (DisallowedHost, DisallowedHost("x"), None)}))

    def test_before_send_span_masks_name_and_attributes(self):
        span = before_send_span({"name": "GET /agenda/?token=abc123", "attributes": {
            "http.request.header.authorization": ["Bearer xyz"],
            "db.query.text": "SELECT 1 -- password=hunter2",
            "client.address": "203.0.113.9",
            "sentry.op": "http.server"}}, {})
        self.assertEqual(leaked(span, *SECRETS), [])
        self.assertEqual(span["name"], "GET /agenda/?token=" + FILTERED)
        self.assertEqual(span["attributes"]["sentry.op"], "http.server")

    def test_before_send_span_never_sends_the_raw_span(self):
        class Trap(dict):
            def items(self):
                raise RuntimeError("boom")

        self.assertEqual(before_send_span({"name": "x", "attributes": Trap(password="hunter2")}, {}),
                         {"name": FILTERED, "attributes": {}})


class CapturingTransport(Transport):
    def __init__(self, options=None):
        super().__init__(options)
        self.sent = []

    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.type == "event":
                self.sent.append(item.payload.json)
            elif item.type == "span":
                self.sent.extend(dict(s, type="span") for s in item.payload.json["items"])


class RealClientTests(SimpleTestCase):
    def setUp(self):
        self.transport = CapturingTransport()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sentry_sdk.init(dsn="https://key@sentry.invalid/1", transport=self.transport,
                            default_integrations=False, traces_sample_rate=1.0, **sentry_options())
        self.assertEqual([str(w.message) for w in caught
                          if issubclass(w.category, DeprecationWarning)], [])

    def tearDown(self):
        sentry_sdk.get_client().close()
        sentry_sdk.get_global_scope().set_client(None)

    def test_logger_error_creates_an_event(self):
        logging.getLogger("event.probe").error("Probe %s", "value")
        sentry_sdk.flush()
        events = [e for e in self.transport.sent if e.get("type", "event") == "event"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["logentry"]["message"], "Probe %s")

    def test_local_password_variable_is_scrubbed(self):
        # Built at run time: the source context (code) must not quote it.
        password = "probe-pw-" + str(6 * 7)
        try:
            raise ValueError("boom")
        except ValueError:
            sentry_sdk.capture_exception()
        sentry_sdk.flush()
        self.assertEqual(len(self.transport.sent), 1)
        self.assertEqual(leaked(self.transport.sent, password), [])

    def test_sent_span_is_masked(self):
        with sentry_sdk.start_span(name="GET /agenda/?token=abc123",
                                   attributes={"password": "hunter2", "note": "api_key=k3y"}):
            pass
        sentry_sdk.flush()
        spans = [e for e in self.transport.sent if e.get("type") == "span"]
        self.assertTrue(spans)
        self.assertEqual(leaked(spans, *SECRETS), [])
