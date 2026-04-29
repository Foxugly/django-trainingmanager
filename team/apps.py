from django.apps import AppConfig


class TeamConfig(AppConfig):
    name = "team"

    def ready(self):
        from . import signals  # noqa: F401
