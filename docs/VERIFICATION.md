# Verification report

This is the historical local verification report for **0.1.1**. Current releases
and their checks are available in [GitHub Actions](https://github.com/hitenjadeja/django-admin-htmx/actions)
and [GitHub Releases](https://github.com/hitenjadeja/django-admin-htmx/releases).
See [RELEASING.md](RELEASING.md) for the current distribution workflow.

Updated 2026-09-08. Package version 0.1.1, stable vendored HTMX 4.0.0. The source suite contains **49 backend/integration tests and 19 real-browser scenarios**, with multiple workflow assertions per browser scenario. No browser tests are mocked or skipped in the final matrix.

## Final test matrix

| Django | Python | Result | Evidence |
|---|---|---|---|
| 5.2.17 | 3.13.0 | 68 passed in 55.31s | [JUnit](../evidence/django52.xml) · [log](../evidence/django52-tests.txt) |
| 6.0.8 | 3.13.0 | 68 passed in 60.44s (0:01:00) | [JUnit](../evidence/django60.xml) · [log](../evidence/django60-tests.txt) |
| 6.1.1 | 3.13.0 | 68 passed in 64.93s (0:01:04) | [JUnit](../evidence/django61.xml) · [log](../evidence/django61-tests.txt) |
| 6.1.1 | 3.12.7 | 68 passed in 62.68s (0:01:02) | [JUnit](../evidence/python312-django61.xml) · [log](../evidence/python312-django61-tests.txt) |

**272 passing source-suite executions** across four environments. Browser engine: Chromium 151.0.7922.34 (Playwright 1.62.0), macOS arm64. Tests use SQLite, an actual Django live server, real form submissions and local static assets. Browser errors are asserted absent.

## Independent wheel installations

Each generated project has its own non-editable environment, Django installation, settings, models, migrations, database and collected static assets. The test command runs from inside the fresh project with PYTHONPATH unset, outside the source-package import path. It asserts the installed module comes from site-packages, checks HTMX 4.0.0, then performs login, prepopulation, autocomplete, inline addition and a persisted save without reloading the document.

| Django | Backend + browser | Verified import | Evidence |
|---|---|---|---|
| 5.2.17 | Passed | `.venvs/fresh-django52/lib/python3.13/site-packages/admin_htmx/__init__.py` | [log](../fresh_install/django52/verification-output.txt) |
| 6.0.8 | Passed | `.venvs/fresh-django60/lib/python3.13/site-packages/admin_htmx/__init__.py` | [log](../fresh_install/django60/verification-output.txt) |
| 6.1.1 | Passed | `.venvs/fresh-django61/lib/python3.13/site-packages/admin_htmx/__init__.py` | [log](../fresh_install/django61/verification-output.txt) |

**3 additional fresh-project tests passed.** Each project also passed migrations, Django system checks and collectstatic. Desktop/mobile saved-state screenshots from each installation are in the [walkthrough](WALKTHROUGH.md). The reports record the exact wheel SHA-256 and installed import path.

Verified wheel: `dist/django_admin_htmx-0.1.1-py3-none-any.whl`

SHA-256: `9f34016b5e2447edcb6f610d2c2381dc55a2d5956c435ed2f226a99aa3369e6c`

[Artifact sizes and checksums](../evidence/artifacts.json), [fresh-install machine-readable report](../evidence/fresh-install.json), [test matrix JSON](../evidence/test-matrix.json), [HTMX version/provenance](../evidence/htmx-version.json).

Wheel inspection confirmed the Python app, template override, template tag, JavaScript, pinned HTMX source and both licenses are present; example code, test files and databases are absent from the wheel. The wheel contains no CSS files. The source distribution includes the example, tests/conftest and reproducible verification scripts. Build artifacts are under dist/ and are not remotely published.

## Default Django appearance restored in 0.1.1

The custom theme, mobile navigation/filter buttons, sticky save bar, progress bar and floating toast have been removed. Django's own stylesheet set, cascade order, colours, fonts, layout and responsive breakpoints are preserved. The loader also removes obsolete stylesheets when navigating away from a page and waits for new styles before initializing widgets.

Pending submissions use the existing controls' disabled state and a visually hidden live region. Request errors use Django's standard errornote class. HTMX 4 navigation, forms, widget lifecycle, focus management, CSRF, permissions, history and native fallbacks remain active.

Four visual scenarios cover desktop/mobile and light/dark themes, each comparing nine pages with Django's unmodified admin/base.html. The baseline has no library scripts or stylesheet. Tests require identical stylesheet order, computed styles and element geometry, and matching screenshots (up to 100 native-control corner pixels may differ by at most 8/255 per channel due to browser antialiasing). They also assert that navigation uses HTMX requests and the original enhanced document stays loaded. See [paired native/enhanced evidence](STYLE_PARITY.md).

Earlier lifecycle, nonce and Django 5.2 password-widget fixes remain covered by the full regression suite. The initial custom responsive styling described in the 0.1.0 task history is superseded by this default-appearance contract.

## Scope and limits

See [COVERAGE.md](COVERAGE.md) for the feature-to-test mapping and precise boundaries. Related-object popups intentionally use Django's native protocol; autocomplete retains Select2 AJAX. Unknown custom media default to native pages unless explicitly opted in. Basic no-JavaScript CRUD is verified; JS-specific widgets still require JS. Files must be reselected after validation. Custom non-200 validation responses, non-attachment non-HTML actions, arbitrary third-party themes/editors, non-Chromium browsers, screen readers, other locales/RTL and database-specific behavior are not claimed as exhaustively verified.

These limits are documented integration boundaries; the implemented and tested core admin flows are complete. No remote push, package publication or deployment was requested or performed.
