# Django admin + HTMX 4

An installable Django app that progressively enhances Django's own admin with HTMX 4.0.0 navigation and submissions, responsive layouts, and a managed lifecycle for stock admin widgets. Django continues to render forms, validate data, enforce permissions and CSRF, and execute ModelAdmin hooks.

Implementation and verification are in progress. See [the plan](docs/PLAN.md) and [capability matrix](docs/COVERAGE.md) for current measured status.

## Install

```sh
pip install django-admin-htmx-0.1.0-py3-none-any.whl
```

```python
INSTALLED_APPS = [
    "admin_htmx",  # before django.contrib.admin
    "django.contrib.admin",
    # your usual Django apps
]
MIDDLEWARE = [
    "admin_htmx.middleware.AdminHtmxMiddleware",  # before compression/cache middleware
    # your usual middleware, including authentication and CSRF
]
```

Use Django's normal admin URLs and ModelAdmin classes. Run `collectstatic` for production. All HTMX assets are vendored; no CDN or Node build is needed. Supported dependency range: Django 5.2 through 6.1, Python 3.12+. Exact verified environments and limitations will be recorded with the release evidence.
