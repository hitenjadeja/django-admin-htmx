# Verification report

Completed 2026-09-07. Package version 0.1.0, stable vendored HTMX 4.0.0. The source suite contains **49 backend/integration tests and 15 real-browser scenarios**, with multiple workflow assertions per browser scenario. No browser tests are mocked or skipped in the final matrix.

## Final test matrix

| Django | Python | Result | Evidence |
|---|---|---|---|
| 5.2.17 | 3.13.0 | 64 passed in 28.05s | [JUnit](../evidence/django52.xml) · [log](../evidence/django52-tests.txt) |
| 6.0.8 | 3.13.0 | 64 passed in 32.35s | [JUnit](../evidence/django60.xml) · [log](../evidence/django60-tests.txt) |
| 6.1.1 | 3.13.0 | 64 passed in 36.42s | [JUnit](../evidence/django61.xml) · [log](../evidence/django61-tests.txt) |
| 6.1.1 | 3.12.7 | 64 passed in 35.31s | [JUnit](../evidence/python312-django61.xml) · [log](../evidence/python312-django61-tests.txt) |

**256 passing source-suite executions** across four environments. Browser engine: Chromium 151.0.7922.34 (Playwright 1.62.0), macOS arm64. Tests use SQLite, an actual Django live server, real form submissions and local static assets. Browser errors are asserted absent.

## Independent wheel installations

Each generated project has its own non-editable environment, Django installation, settings, models, migrations, database and collected static assets. The test command runs from inside the fresh project with PYTHONPATH unset, outside the source-package import path. It asserts the installed module comes from site-packages, checks HTMX 4.0.0, then performs login, prepopulation, autocomplete, inline addition and a persisted save without reloading the document.

| Django | Backend + browser | Verified import | Evidence |
|---|---|---|---|
| 5.2.17 | Passed | `.venvs/fresh-django52/lib/python3.13/site-packages/admin_htmx/__init__.py` | [log](../fresh_install/django52/verification-output.txt) |
| 6.0.8 | Passed | `.venvs/fresh-django60/lib/python3.13/site-packages/admin_htmx/__init__.py` | [log](../fresh_install/django60/verification-output.txt) |
| 6.1.1 | Passed | `.venvs/fresh-django61/lib/python3.13/site-packages/admin_htmx/__init__.py` | [log](../fresh_install/django61/verification-output.txt) |

**3 additional fresh-project tests passed.** Each project also passed migrations, Django system checks and collectstatic. Desktop/mobile saved-state screenshots from each installation are in the [walkthrough](WALKTHROUGH.md). The reports record the exact wheel SHA-256 and installed import path.

Verified wheel: `dist/django_admin_htmx-0.1.0-py3-none-any.whl`  
SHA-256: `e20e16aa0c28c2f6b4aa33eaf5d680cf48694928ca94ae7fe2bc69259cdd5559`

[Artifact sizes and checksums](../evidence/artifacts.json), [fresh-install machine-readable report](../evidence/fresh-install.json), [test matrix JSON](../evidence/test-matrix.json), [HTMX version/provenance](../evidence/htmx-version.json).

Wheel inspection confirmed the Python app, template override, template tag, CSS, JavaScript, pinned HTMX source and both licenses are present; example code, test files and databases are absent from the wheel. The source distribution includes the example, tests/conftest and reproducible verification scripts. Build artifacts are under dist/ and are not remotely published.

## UI/UX findings and corrections

- Select2 loaded after a previous page's jquery.init had lost its temporary global. The loader now briefly bridges Django's jQuery only while Select2 media load, and restores it afterward.
- Stock widget scripts assume fresh documents. Per-page initialization/cleanup now covers inlines, calendars, selectors, actions, filters, themes, cancellation and prepopulation. Repeated-navigation tests check widget counts and global-listener counts.
- Django 6.1's nested changelist retained a desktop filter width on mobile. The mobile layout now expands the table/search area, keeps filters collapsible and confines scrolling to the table.
- The sidebar retained a desktop offset on mobile. Its mobile position and usable width are now asserted.
- Django's viewport-based text-field width clipped controls inside padded form rows. Form controls now fit their containers; the browser checks the actual field width.
- A nonce-only script policy needed the active document nonce retained across later script loads. This is implemented and tested without unsafe-eval.
- Django 5.2 includes a legacy unusable-password script removed in 6.x. It has an explicit version-aware lifecycle entry, tested via user creation and password reset.
- Response middleware order is reversed by Django. GZip integration is verified, and a system check warns when compression/ETag/cache middleware would run before the adapter can transform HTML.
- Loading/live-region, focused errors, retained drafts after failures, successful retry, duplicate-submit prevention, keyboard menu closing, browser history, permission boundaries and native fallback have browser evidence.

## Scope and limits

See [COVERAGE.md](COVERAGE.md) for the feature-to-test mapping and precise boundaries. Related-object popups intentionally use Django's native protocol; autocomplete retains Select2 AJAX. Unknown custom media default to native pages unless explicitly opted in. Basic no-JavaScript CRUD is verified; JS-specific widgets still require JS. Files must be reselected after validation. Custom non-200 validation responses, non-attachment non-HTML actions, arbitrary third-party themes/editors, non-Chromium browsers, screen readers, other locales/RTL and database-specific behavior are not claimed as exhaustively verified.

These limits are documented integration boundaries; the implemented and tested core admin flows are complete. No remote push, package publication or deployment was requested or performed.
