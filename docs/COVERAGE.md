# Capability and test coverage

The inventory was created before implementation. Version 0.1.1 (2026-09-08) restores Django's default appearance; the custom theme and extra mobile controls from 0.1.0 are removed. The final suite maps each requested core capability to an actual check. This is coverage of representative stock admin behavior and the documented integration contract, not a claim to have exhaustively tested every possible ModelAdmin override or third-party widget.

See VERIFICATION.md for the measured version matrix, exact totals, wheel-install results and limits. `tests/test_admin.py` contains backend/security/integration tests; `tests/test_middleware.py` and `tests/test_configuration.py` add focused unit tests; `tests/test_browser.py` runs actual Chromium against a live Django server and checks JavaScript errors. `fresh_install/*/library/tests.py` verifies installed-wheel behavior in independent Django projects.

## Python coverage gate

Pre-commit and every backend CI matrix job run:

```sh
python -m pytest tests -m 'not browser' --cov -q
```

The suite combines focused unit tests with integration tests using Django's test
client, database, admin forms, permissions, CSRF handling and audit log. Coverage
measures every Python module in `src/admin_htmx/`, including unexecuted modules;
example code, tests, templates and JavaScript are outside that Python source
scope. No package modules are omitted. `pyproject.toml` enables branch measurement
and requires at least 95% total coverage (statements and branch destinations
combined), with two decimal places and missing lines/branches shown on failure.

Chromium end-to-end and installed-wheel integration checks remain separate CI
requirements. They exercise browser behavior and packaging; the Python percentage
does not claim JavaScript or template coverage. Run `python -m coverage html`
after a coverage run for a browsable local report in `htmlcov/`.

Coverage-gate verification on 2026-09-09, separate from historical release evidence:

| Runtime | Unit + Django integration tests | Python coverage, including branches |
|---|---|---|
| Python 3.13.3 / Django 5.2 | 129 passed | 98.91% |
| Python 3.13.3 / Django 6.0 | 129 passed | 98.36% |
| Python 3.14.3 / Django 6.1.1 | 129 passed | 98.36% |

The complete source suite also passed all 151 tests, including 22 Chromium cases,
on Python 3.14.3 / Django 6.1.1. A deliberately incomplete coverage run (only the
configuration unit tests) passed its nine tests but exited with failure at 20.77%
coverage, confirming that the 95% gate rejects insufficient coverage.

## Capability inventory

| Capability | Backend/integration checks | Real browser checks |
|---|---|---|
| Login/logout | Invalid/valid login, staff gate, POST-only logout, authenticated redirects | Error → login → dashboard without document reload; logout finish; expired session redirects back to login with next URL |
| Passwords | Own-password validation/success, session retained | Mobile wrong-password feedback and success; UserAdmin creates a user and resets that user's password |
| Dashboard/app index | Full document and enhanced responses; stock context | Dashboard, app index, breadcrumbs and sidebar; desktop/mobile screenshots |
| Custom AdminSite | Independent editorial namespace and admin URLs | Editorial navigation, different branding, custom report view, custom-media lifecycle |
| Changelists | Search/no results, filter states, ordering/facets | Search, filter, facets, sort, pagination, date hierarchy, preserved filter URLs |
| Add/change | Valid writes and LogEntry, field/nonfield/uniqueness validation | Prepopulation, autocomplete, validation focus and retained values, save and continue, return to list |
| Save variants | Save, continue, add another, save-as-new, preserved filters | All four save variants; copied and original objects both retained |
| Deletion/history | Confirmation, protected relations, delete audit/history | History, single deletion confirm/finish/cancel; protected deletion page |
| Actions | Custom mutation, intermediate form, download, delete selected | Select page/select across pages; publish, archive confirm/finish, delete selected confirm/finish, actual CSV download bytes |
| List editable | Valid and invalid writes, invalid DB values rejected | Invalid-price errors, corrected save, success message |
| Inlines | Tabular/stacked save; invalid child rolls back parent; existing child update/delete | Both inline styles, dynamic add/remove, management counts, repeated visits, persisted children after save |
| Related widgets | Autocomplete permissions and popup response protocol | Autocomplete query/select, add popup, raw-ID lookup, change popup, delete popup and result reflected in opener |
| Widgets | Date/time/file/M2M fields persisted | Calendar open/today, prepopulated slug, filtered multi-select, selected options submitted, collapsible form sections present, user/group permissions widgets |
| Uploads | Multipart bytes stored; attachment-clear clears model field | Actual file chooser upload, validation/reselection, saved contents |
| Security | CSRF denied/accepted; permissions/view-only/nonstaff; escaped object content; adapter headers don't hijack another HTMX client | Read-only UI; lost session; nonce-only script policy survives HTMX navigation without unsafe-eval |
| Middleware | GZip response contains enhanced HTML; ordering check; disabled mode/non-admin isolation | Same-document sentinel survives navigations and POST/redirect/GET flows |
| Reactive UX | Server remains source of validation/errors | Delayed visible progress/status on desktop and mobile; light/dark and reduced motion; fast-request/network-failure timer cancellation; slow stylesheet hydration; native disabled submit controls; one request for duplicate navigation/submission; POST/redirect/GET loading; failed response retains draft with a standard Django errornote; recovery save; focus on errors/landmark |
| History/lifecycle | Full documents for direct and enhanced requests | Browser back/forward; no localStorage HTML snapshots; repeated widget counts and global-listener count stay stable |
| Responsive UX | Stock markup and semantics preserved | 1440px desktop and 390px mobile; Django's original breakpoints, navigation, filters and form layout; native and enhanced pages are compared directly |
| Default appearance | Package contains no CSS; base template leaves Django's responsive block untouched | Nine page states in each desktop/mobile × light/dark scenario; exact stylesheet order, visible computed styles and geometry; pixel comparison with a small native-control antialiasing allowance; real HTMX requests and persistent document marker |
| Custom media/templates | Stock inheritance and script inventory/explicit opt-in | Unknown media gets native navigation; opted-in once script persists across HTMX navigation/history without rerunning |
| No JavaScript | Same Django HTML forms/views | Login, create author, confirmation and deletion with JavaScript disabled |
| Distribution | Wheel/sdist assets and metadata; check/migrations/collectstatic | Independent wheel import from site-packages; fresh project's own models; HTMX login, widgets, inline, save, desktop/mobile captures |

## Deliberate compatibility boundaries

- Related popups remain native browser windows using Django's protocol; autocomplete retains Select2's AJAX transport. Parent-page lifecycle and the returned values are tested.
- Unknown custom scripts default to native pages. Opted-in scripts must supply their own cleanup and initialization contract; arbitrary rich text editors and third-party themes are not automatically guaranteed.
- Native no-JavaScript CRUD is verified for ordinary fields. Autocomplete, filtered selector interactions and calendar shortcuts inherently require JavaScript, just as in stock Django.
- Server 4xx/5xx responses leave the current page intact with an error message. Stock Django validation uses HTTP 200 and swaps normally. Custom views using 422 for form errors should use a custom HTMX integration or native opt-out.
- Validation responses clear file inputs; the browser requires reselection. Unknown non-HTML POST results other than attachment downloads need a custom integration.
- The browser suite is Chromium on macOS, English locale. Firefox/WebKit, screen readers, other locales/RTL, exotic CSP directives and third-party admin themes are not claimed as verified.
- Tests use SQLite. Database-specific application behavior, race conditions between different users, password-reset email delivery, and arbitrary custom admin endpoints remain the integrating application's responsibility.

## Primary-source decisions (checked 2026-09-07)

- [Django supported versions](https://www.djangoproject.com/download/) listed 5.2 LTS (5.2.17), 6.0 (6.0.8), and 6.1 (6.1.1). Those are the tested series; older unsupported releases and future releases are outside the dependency range.
- [Django admin reference](https://docs.djangoproject.com/en/6.1/ref/contrib/admin/) informed the inventory of ModelAdmin options, media, inline forms, template blocks, AdminSite namespaces and extension points. Installed Django source was inspected for lifecycle behavior on each tested series.
- [HTMX announcement](https://htmx.org/) and [HTMX 4 installation](https://four.htmx.org/docs#installation) identify 4.0.0 as released, with npm latest intentionally remaining on 2.x for compatibility. The exact 4.0.0 distribution is bundled.
- [HTMX 4 migration guide](https://four.htmx.org/docs#migrating-from-htmx-2x-to-4x) documents explicit inheritance, colon-separated events, swapping error statuses by default and server-backed history. The adapter uses explicit per-control attributes and intercepts error responses deliberately.
- [HTMX 4 response headers](https://four.htmx.org/docs#response-headers) informed non-3xx HX-Location redirects. The adapter does not repeat POST operations to obtain a redirected page or download.
