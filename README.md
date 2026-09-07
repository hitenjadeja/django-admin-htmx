# Django admin + HTMX 4

An installable Django app that makes Django's own admin responsive and reactive with **HTMX 4.0.0**. Existing ModelAdmin classes, forms, permissions, CSRF protection, messages, actions and audit logs remain authoritative. No admin model registry replacement, application database tables, CDN, or JavaScript build step is required.

## Install and integrate

Install the built wheel (this project has not been published remotely):

```sh
python -m pip install dist/django_admin_htmx-0.1.0-py3-none-any.whl
```

Add the app **before** Django admin, and append the middleware to your existing middleware list:

```python
INSTALLED_APPS = [
    "admin_htmx",
    "django.contrib.admin",
    # the rest of your existing applications
]

MIDDLEWARE = [
    # your existing security, sessions, CSRF, authentication, and other middleware
    "admin_htmx.middleware.AdminHtmxMiddleware",
]
```

Keep your existing URLs, including custom AdminSite instances:

```python
from django.contrib import admin
from django.urls import path

urlpatterns = [path("admin/", admin.site.urls)]
```

Run `python manage.py check` and `python manage.py collectstatic --noinput`. Serve `STATIC_ROOT` using your usual production static-file server. The middleware must appear **after** GZipMiddleware, ConditionalGetMiddleware and UpdateCacheMiddleware when used: response middleware runs in reverse order, so HTML must be enhanced before compression, ETags or caching. System checks flag incorrect app/middleware ordering.

Do not load another HTMX core on enhanced admin pages. Keep `{{ block.super }}` when overriding `extrahead` or `responsive` in admin templates. The package has no migrations and does not change your models.

## What is enhanced

- Login/logout, password changes, dashboard, app index and sidebar navigation.
- Changelist search, filters/facets, ordering, date hierarchy, pagination and list editing.
- Add/change/delete/history, validation errors, preserved filters and every standard save variant.
- Bulk selection, select across pages, actions, intermediate confirmations and file downloads.
- Tabular/stacked inlines, date/time widgets, prepopulated fields, uploads, related widgets and filtered multi-selects.
- Visible loading and error feedback, duplicate-submit prevention, focus recovery and browser back/forward.
- Mobile navigation/filter controls, usable form widths and contained horizontal table scrolling.

Django's related-object popups retain their native opener/dismiss protocol. Autocomplete retains Django's Select2 AJAX endpoint. These controls are initialized correctly after HTMX navigation rather than being replaced with new protocols.

HTMX 4.0.0 is a **stable release**, explicitly pinned and vendored with its license. The official site announced its release while deliberately keeping npm's `latest` alias on the 2.x line. This project uses HTMX 4's APIs and colon-separated lifecycle events. Its default history behavior re-fetches pages from the server; admin HTML is not cached in localStorage.

## Compatibility and extension points

Dependency range: **Django >=5.2,<6.2**, **Python >=3.12**. Tested release/runtime details, exact test results and install evidence are in [VERIFICATION.md](docs/VERIFICATION.md). The maintained browser suite runs in Chromium; other engines and locales are not claimed as verified.

Custom ModelAdmin and AdminSite subclasses work normally. A custom template using stock media can use HTMX automatically. Pages with unknown scripts default to native navigation so their existing lifecycle still works. Developers can opt compatible scripts in using `data-admin-htmx-load="once"` or `"page"`, then initialize/destroy custom controls on `admin-htmx:load` and `admin-htmx:before-swap`. See [the architecture and extension contract](docs/ARCHITECTURE.md).

Use `data-admin-htmx="off"` on a control/wrapper, `hx-boost="false"`, or `ADMIN_HTMX_ENABLED = False` to opt out. Basic native HTML login and CRUD remain usable without JavaScript. JavaScript-specific widgets retain Django's usual no-JavaScript limitations. File inputs must be reselected after server validation, as with native Django.

A `csp_nonce` template context value is supported. With Django's CSP middleware, enable the `django.template.context_processors.csp` context processor. The loader keeps the active document's nonce for scripts loaded during later swaps. The browser suite verifies a nonce-only `script-src` policy without `unsafe-eval`. Projects with other CSP directives, rich text editors, custom themes, custom HTMX fragments, or complete base-template replacements should test their own integration.

## Run the example

The repository includes a catalog admin with book/author/tag/edition models, both inline types, file uploads, list editing, actions, user/group administration, a second AdminSite, and custom-media integration examples.

```sh
# From this project, use a working Python 3.12+ interpreter:
python -m venv .venvs/dev
.venvs/dev/bin/python -m pip install -e '.[test]'
.venvs/dev/bin/python example/manage.py migrate
.venvs/dev/bin/python example/manage.py seed_demo
.venvs/dev/bin/python example/manage.py runserver 127.0.0.1:8791
```

Open `/admin/` or `/editorial/`. The seed command creates local demonstration accounts `admin` and `viewer`, both with password `Local-demo-2026!`. The viewer has read-only catalog permissions. The seed command and example settings are for local development only.

## Test, build and reproduce the wheel installation

```sh
mkdir -p .cache/ms-playwright .cache/tmp
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" .venvs/dev/bin/python -m playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" .venvs/dev/bin/python -m pytest tests -q

# Build the wheel and source archive. uv is used by the reproducible build/install script.
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" uv build --out-dir dist
.venvs/dev/bin/python scripts/verify_fresh_install.py
```

`verify_fresh_install.py` builds the package, creates three independent Django projects and environments under `fresh_install/` and `.venvs/`, installs the **wheel** (not an editable checkout), runs migrations/checks/collectstatic, checks the package import path and exercises login, prepopulation, autocomplete, inlines and a save in real Chromium. It records JSON, test logs and desktop/mobile screenshots. `--skip-build` reuses the existing wheel.

Prepared version environments in this workspace are `.venvs/django52`, `.venvs/django60` and `.venvs/django61`; `scripts/test_matrix.py` runs the complete suite against each. To recreate them, create a virtual environment for each series and install `-e '.[test]'` with `Django==5.2.*`, `Django==6.0.*`, or `Django==6.1.*`, respectively. The additional `.venvs/python312-django61` verifies Python 3.12.

Set `ADMIN_HTMX_SCREENSHOTS=1` during browser tests to regenerate the screenshot walkthrough. All project environments, caches, tests, example/fresh projects, artifacts and evidence are local to this folder. No remote service or publication is needed.

- [Capability and test matrix](docs/COVERAGE.md)
- [Measured verification and limitations](docs/VERIFICATION.md)
- [Ordered screenshot walkthrough](docs/WALKTHROUGH.md)
- [Task plan](docs/PLAN.md)

## Upstream references

[Django supported releases](https://www.djangoproject.com/download/), [Django admin reference](https://docs.djangoproject.com/en/6.1/ref/contrib/admin/), [HTMX 4 documentation](https://four.htmx.org/docs), [HTMX 4 migration changes](https://four.htmx.org/docs#migrating-from-htmx-2x-to-4x). Checked on 2026-09-07.

License: BSD-3-Clause. The vendored HTMX source retains its own BSD Zero Clause license in `admin_htmx/static/admin_htmx/vendor/HTMX-LICENSE`.
