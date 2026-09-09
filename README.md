# Django admin + HTMX 4

[![CI](https://github.com/hitenjadeja/django-admin-htmx/actions/workflows/ci.yml/badge.svg)](https://github.com/hitenjadeja/django-admin-htmx/actions/workflows/ci.yml)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-blue)](https://github.com/hitenjadeja/django-admin-htmx/blob/main/LICENSE)

An installable Django app that adds **HTMX 4.0.0** navigation to Django's own admin while retaining its default appearance. Existing ModelAdmin classes, forms, permissions, CSRF protection, messages, actions and audit logs remain authoritative. No admin model registry replacement, application database tables, CDN, or JavaScript build step is required.

## Install and integrate

The project is in beta. Install the pinned GitHub version in your project's
virtual environment (PyPI publication is planned separately):

```sh
python -m pip install "django-admin-htmx @ git+https://github.com/hitenjadeja/django-admin-htmx.git@v0.1.2"
```

Or download the wheel from the [0.1.2 GitHub release](https://github.com/hitenjadeja/django-admin-htmx/releases/tag/v0.1.2)
and install it with `python -m pip install /path/to/django_admin_htmx-0.1.2-py3-none-any.whl`.
For uv, use `uv add "django-admin-htmx @ git+https://github.com/hitenjadeja/django-admin-htmx.git@v0.1.2"`.
Pin the version in your dependency file or lockfile. See the
[existing-project testing guide](https://github.com/hitenjadeja/django-admin-htmx/blob/main/docs/INTEGRATION.md)
for checks, upgrades and rollback.

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

Do not load another HTMX core on enhanced admin pages. Keep `{{ block.super }}` when overriding `extrahead` in admin templates. The package has no migrations and does not change your models.

## How it works

HTMX sends eligible admin links and forms to Django's existing URLs without a
full browser reload. Django still renders complete HTML pages and owns
permissions, CSRF checks, validation, saving, messages and audit logging. The
browser swaps the incoming `<body>`, synchronizes Django's stylesheets and
initializes the new page's widgets. Successful admin redirects become
`HX-Location` responses followed by a GET.

Validation errors display Django's returned form. HTTP errors and network
failures before a swap keep the current form visible with an error message;
failed POSTs are never automatically retried. Session-expiry redirects show
Django's login page.

See [the request flow and implementation map](docs/ARCHITECTURE.md#how-it-works)
and [error handling and recovery](docs/ARCHITECTURE.md#error-handling) for the
diagram, failure cases and compatibility boundaries.

## Default Django appearance

The package preserves Django's colours, fonts, spacing, widgets, navigation and responsive breakpoints. Django's stylesheets keep their original order, and obsolete page styles are removed after navigation. One small local stylesheet targets only the transient loading indicator. Existing project branding and template/style customizations remain your own.

Requests announce “Loading…” to assistive technology immediately. After 200 ms, a thin top progress bar and a visible status badge appear until the page and its widgets are ready. These use Django's colors, respect reduced motion and do not shift layout or intercept clicks. Existing submit controls are temporarily disabled, and overlapping requests are dropped. Request failures clear the loading feedback and use Django's existing `errornote` styling; normal validation and success messages remain Django's own. See the [loading-feedback walkthrough](docs/LOADING_FEEDBACK.md).

Desktop/mobile screenshots in both light and dark modes are compared with Django's original `admin/base.html`, with the library disabled. Those checks also verify that the enhanced document stays loaded and navigation uses actual HTMX requests. See [the visual comparison evidence](https://github.com/hitenjadeja/django-admin-htmx/blob/main/docs/STYLE_PARITY.md).

## What is enhanced

- Login/logout, password changes, dashboard, app index and sidebar navigation.
- Changelist search, filters/facets, ordering, date hierarchy, pagination and list editing.
- Add/change/delete/history, validation errors, preserved filters and every standard save variant.
- Bulk selection, select across pages, actions, intermediate confirmations and file downloads.
- Tabular/stacked inlines, date/time widgets, prepopulated fields, uploads, related widgets and filtered multi-selects.
- Visible and accessible loading feedback, native disabled submit controls, Django-styled error feedback, duplicate-submit prevention, focus recovery and browser back/forward.
- Django's own desktop/mobile layout, theme toggle, navigation and filter controls.

Django's related-object popups retain their native opener/dismiss protocol. Autocomplete retains Django's Select2 AJAX endpoint. These controls are initialized correctly after HTMX navigation rather than being replaced with new protocols.

HTMX 4.0.0 is a **stable release**, explicitly pinned and vendored with its license. The official site announced its release while deliberately keeping npm's `latest` alias on the 2.x line. This project uses HTMX 4's APIs and colon-separated lifecycle events. Its default history behavior re-fetches pages from the server; admin HTML is not cached in localStorage.

## Compatibility and extension points

Dependency range: **Django >=5.2,<6.2**, **Python >=3.12**. Tested release/runtime details, exact test results and install evidence are in [VERIFICATION.md](https://github.com/hitenjadeja/django-admin-htmx/blob/main/docs/VERIFICATION.md). The maintained browser suite runs in Chromium; other engines and locales are not claimed as verified.

Custom ModelAdmin and AdminSite subclasses work normally. A custom template using stock media can use HTMX automatically. Pages with unknown scripts default to native navigation so their existing lifecycle still works. Developers can opt compatible scripts in using `data-admin-htmx-load="once"` or `"page"`, then initialize/destroy custom controls on `admin-htmx:load` and `admin-htmx:before-swap`. See [the architecture and extension contract](https://github.com/hitenjadeja/django-admin-htmx/blob/main/docs/ARCHITECTURE.md).

Use `data-admin-htmx="off"` on a control/wrapper, `hx-boost="false"`, or `ADMIN_HTMX_ENABLED = False` to opt out. Basic native HTML login and CRUD remain usable without JavaScript. JavaScript-specific widgets retain Django's usual no-JavaScript limitations. File inputs must be reselected after server validation, as with native Django.

A `csp_nonce` template context value is supported. With Django's CSP middleware, enable the `django.template.context_processors.csp` context processor. The loader keeps the active document's nonce for scripts loaded during later swaps. The browser suite verifies a nonce-only `script-src` policy without `unsafe-eval`. Projects with other CSP directives, rich text editors, custom themes, custom HTMX fragments, or complete base-template replacements should test their own integration.

## Run the example

The repository includes a catalog admin with book/author/tag/edition models, both inline types, file uploads, list editing, actions, user/group administration, a second AdminSite, and custom-media integration examples.

```sh
# From this project, use a working Python 3.12+ interpreter:
python -m venv .venvs/dev
.venvs/dev/bin/python -m pip install -e '.[test,dev]'
.venvs/dev/bin/python example/manage.py migrate
.venvs/dev/bin/python example/manage.py seed_demo
.venvs/dev/bin/python example/manage.py runserver 127.0.0.1:8791
```

Open `/admin/` or `/editorial/`. The seed command creates local demonstration accounts `admin` and `viewer`, both with password `Local-demo-2026!`. The viewer has read-only catalog permissions. The seed command and example settings are for local development only.

## Test, build and reproduce the wheel installation

```sh
mkdir -p .cache/ms-playwright .cache/tmp
.venvs/dev/bin/python -m pytest tests -m 'not browser' --cov -q
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" .venvs/dev/bin/python -m playwright install chromium
PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright" .venvs/dev/bin/python -m pytest tests -q

# Build the wheel and source archive. uv is used by the reproducible build/install script.
UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp" uv build --out-dir dist
.venvs/dev/bin/python scripts/verify_fresh_install.py
```

`verify_fresh_install.py` builds the package, creates three independent Django projects and environments under `fresh_install/` and `.venvs/`, installs the **wheel** (not an editable checkout), runs migrations/checks/collectstatic, checks the package import path and exercises login, prepopulation, autocomplete, inlines and a save in real Chromium. It records JSON, test logs and desktop/mobile screenshots. `--skip-build` reuses the existing wheel.

Prepared version environments in this workspace are `.venvs/django52`, `.venvs/django60` and `.venvs/django61`; `scripts/test_matrix.py` runs the complete suite against each. To recreate them, create a virtual environment for each series and install `-e '.[test]'` with `Django==5.2.*`, `Django==6.0.*`, or `Django==6.1.*`, respectively. The additional `.venvs/python312-django61` verifies Python 3.12.

Version 0.1.1 removed the custom theme from the initial 0.1.0 build. Version 0.1.2 adds open source distribution and release tooling. See the [changelog](https://github.com/hitenjadeja/django-admin-htmx/blob/main/CHANGELOG.md). Reload any already-open admin pages after an upgrade.

Set `ADMIN_HTMX_SCREENSHOTS=1` during browser tests to regenerate the screenshot walkthrough. All project environments, caches, tests, example/fresh projects, artifacts and evidence are local to this folder. No remote service or publication is needed.

- [Capability and test matrix](https://github.com/hitenjadeja/django-admin-htmx/blob/main/docs/COVERAGE.md)
- [Measured verification and limitations](https://github.com/hitenjadeja/django-admin-htmx/blob/main/docs/VERIFICATION.md)
- [Ordered screenshot walkthrough](https://github.com/hitenjadeja/django-admin-htmx/blob/main/docs/WALKTHROUGH.md)
- [Task plan](https://github.com/hitenjadeja/django-admin-htmx/blob/main/docs/PLAN.md)

## Contributing and releases

See [CONTRIBUTING.md](https://github.com/hitenjadeja/django-admin-htmx/blob/main/CONTRIBUTING.md),
[SECURITY.md](https://github.com/hitenjadeja/django-admin-htmx/blob/main/SECURITY.md),
and [AGENTS.md](https://github.com/hitenjadeja/django-admin-htmx/blob/main/AGENTS.md).
Claude follows the same instructions through `CLAUDE.md`.

The version is declared in `src/admin_htmx/__init__.py`; tags use `vX.Y.Z`.
During 0.x, minor versions may introduce breaking changes, while patch releases
preserve the integration contract. Release notes are maintained in the changelog.

GitHub Actions runs backend tests across Python 3.12–3.14 and Django 5.2, 6.0 and
6.1, plus Chromium tests and fresh-wheel integration on each Django series.
Workflows use standard Ubuntu runners, pinned action commits and seven-day
distribution artifact retention. Standard hosted-runner minutes are free for
public repositories; storage has separate allowances.

[The release guide](https://github.com/hitenjadeja/django-admin-htmx/blob/main/docs/RELEASING.md)
documents GitHub releases, the separate manual TestPyPI/PyPI workflow and the
later Django Packages listing. A normal push or GitHub release does not publish
anything to PyPI.

## Upstream references

[Django supported releases](https://www.djangoproject.com/download/), [Django admin reference](https://docs.djangoproject.com/en/6.1/ref/contrib/admin/), [HTMX 4 documentation](https://four.htmx.org/docs), [HTMX 4 migration changes](https://four.htmx.org/docs#migrating-from-htmx-2x-to-4x). Checked on 2026-09-07.

License: BSD-3-Clause. The vendored HTMX source retains its own BSD Zero Clause license in `admin_htmx/static/admin_htmx/vendor/HTMX-LICENSE`.
