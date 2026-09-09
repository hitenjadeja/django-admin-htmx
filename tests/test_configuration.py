"""Configuration diagnostics and template escaping contracts."""

import pytest

from admin_htmx.checks import check_configuration
from admin_htmx.templatetags.admin_htmx import admin_htmx_nonce

ADAPTER = "admin_htmx.middleware.AdminHtmxMiddleware"


@pytest.mark.parametrize("adapter_first", [False, True])
def test_app_order_warning(settings, adapter_first):
    apps = [app for app in settings.INSTALLED_APPS if app != "admin_htmx"]
    apps.insert(0 if adapter_first else len(apps), "admin_htmx")
    settings.INSTALLED_APPS = apps
    warnings = check_configuration(app_configs=None)
    assert ("admin_htmx.W001" in {warning.id for warning in warnings}) is (
        not adapter_first
    )


@pytest.mark.parametrize(
    "wrapper",
    [
        "django.middleware.gzip.GZipMiddleware",
        "django.middleware.http.ConditionalGetMiddleware",
        "django.middleware.cache.UpdateCacheMiddleware",
    ],
)
@pytest.mark.parametrize("correct_order", [False, True])
def test_response_wrapper_order_warning(settings, wrapper, correct_order):
    settings.MIDDLEWARE = [wrapper, ADAPTER] if correct_order else [ADAPTER, wrapper]
    warnings = check_configuration(app_configs=None)
    if correct_order:
        assert warnings == []
    else:
        assert len(warnings) == 1
        assert warnings[0].id == "admin_htmx.W003"
        assert wrapper in warnings[0].msg


def test_nonce_escapes_attribute_content():
    assert admin_htmx_nonce({}) == ""
    assert admin_htmx_nonce({"csp_nonce": None}) == ""
    assert admin_htmx_nonce({"csp_nonce": 'a"&<b>'}) == 'nonce="a&quot;&amp;&lt;b&gt;"'
