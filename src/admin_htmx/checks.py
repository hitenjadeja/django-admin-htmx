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
    adapter = "admin_htmx.middleware.AdminHtmxMiddleware"
    if adapter in settings.MIDDLEWARE:
        for wrapper in ("django.middleware.gzip.GZipMiddleware", "django.middleware.http.ConditionalGetMiddleware", "django.middleware.cache.UpdateCacheMiddleware"):
            if wrapper in settings.MIDDLEWARE and settings.MIDDLEWARE.index(wrapper) > settings.MIDDLEWARE.index(adapter):
                errors.append(Warning(
                    f"Place {adapter} after {wrapper} so HTML is enhanced before response compression/caching.",
                    id="admin_htmx.W003",
                ))
    return errors
