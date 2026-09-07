from django.apps import apps
from django.conf import settings
from django.core.checks import Warning, register


@register()
def check_configuration(app_configs, **kwargs):
    errors = []
    configs = [config.name for config in apps.get_app_configs()]
    if "django.contrib.admin" in configs and configs.index("admin_htmx") > configs.index("django.contrib.admin"):
        errors.append(Warning(
            "Place admin_htmx before django.contrib.admin in INSTALLED_APPS.",
            id="admin_htmx.W001",
        ))
    if "admin_htmx.middleware.AdminHtmxMiddleware" not in settings.MIDDLEWARE:
        errors.append(Warning(
            "Add admin_htmx.middleware.AdminHtmxMiddleware to MIDDLEWARE to enable HTMX navigation.",
            id="admin_htmx.W002",
        ))
    return errors
