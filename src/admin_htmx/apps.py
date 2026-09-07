from django.apps import AppConfig


class AdminHtmxConfig(AppConfig):
    name = "admin_htmx"
    verbose_name = "HTMX admin"

    def ready(self):
        from . import checks  # noqa: F401
