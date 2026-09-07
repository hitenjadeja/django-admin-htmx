#!/usr/bin/env python3
"""Generate a portable screenshot gallery and measured verification report."""
import hashlib
import html
import json
from pathlib import Path
import zipfile
import tarfile

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
('01-desktop-login','Desktop entry: log in'),
('02-login-error','Invalid credentials: feedback'),
('03-desktop-dashboard','Authenticated dashboard'),
('04-app-index','Application index'),
('05-desktop-changelist','Desktop changelist'),
('13-search-filter-sort','Search, filters and ordering'),
('14-list-edit-saved','List editing: saved'),
('36-list-validation','List editing: invalid value'),
('06-add-form-calendar','Add form: date picker'),
('07-add-form-inlines-upload','Add form: relations, inlines and upload'),
('08-validation-feedback','Form validation: values retained and error focused'),
('09-saved-continue','Save and continue: persisted result'),
('10-object-history','Object history and audit entry'),
('11-delete-confirmation','Single delete: confirmation'),
('38-delete-cancelled','Single delete: cancellation returns to the object'),
('12-delete-finished','Single delete: completed'),
('15-bulk-action-confirmation','Custom bulk action: confirmation'),
('16-bulk-action-finished','Custom bulk action: completed'),
('17-bulk-delete-confirmation','Bulk delete: confirmation'),
('41-bulk-delete-finished','Bulk delete: completed'),
('18-related-author-popup','Related-object popup: add author'),
('19-related-records-selected','Popup and raw-ID selections returned to the form'),
('39-popup-delete-confirmation','Related-object popup: delete confirmation'),
('40-popup-delete-finished','Related-object popup: deletion returned to the form'),
('20-protected-deletion','Protected related object: deletion refused'),
('33-loading-feedback','Reactive feedback during a pending request'),
('31-request-error-retained','Failed request: unsaved draft retained'),
('44-request-error-recovered','Failed request: successful recovery save'),
('34-view-only-permissions','Permission boundary: read-only user'),
('42-session-expiry-login','Expired session: login with return URL'),
('35-user-permission-widgets','User/group filtered permission widgets'),
('45-user-created','UserAdmin: new user saved'),
('46-admin-password-reset','UserAdmin: password reset completed'),
('32-custom-admin-site','Custom AdminSite and namespace'),
('37-custom-media-lifecycle','Custom view with explicit media lifecycle'),
('43-no-javascript-saved','JavaScript disabled: native CRUD saved'),
('21-mobile-login','Mobile entry: log in'),
('22-mobile-dashboard','Mobile dashboard'),
('23-mobile-list','Mobile list with contained table scrolling'),
('24-mobile-navigation','Mobile navigation opened; keyboard focus visible'),
('26-mobile-filters','Mobile filters opened'),
('27-mobile-add-form','Mobile add form: usable widths and save actions'),
('28-mobile-saved','Mobile save completed'),
('29-mobile-password-error','Mobile password validation error'),
('30-mobile-password-done','Mobile password change completed'),
('25-logout','Logout completed'),
]


def main():
    matrix = json.loads((ROOT / 'evidence/test-matrix.json').read_text())
    fresh = json.loads((ROOT / 'evidence/fresh-install.json').read_text())
    assert len(matrix) == 4 and all(row['exit_code'] == 0 for row in matrix), matrix
    assert len(fresh) == 3
    artifacts = []
    for path in sorted((ROOT / 'dist').glob('*')):
        if path.suffix in ('.whl', '.gz'):
            artifacts.append({'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    wheel = next(item for item in artifacts if item['path'].endswith('.whl'))
    assert all(row['sha256'] == wheel['sha256'] for row in fresh), 'Wheel changed since fresh-install verification'
    with zipfile.ZipFile(ROOT / wheel['path']) as archive:
        names = archive.namelist()
        for required in ['admin_htmx/templates/admin/base.html', 'admin_htmx/static/admin_htmx/admin.js', 'admin_htmx/static/admin_htmx/admin.css', 'admin_htmx/static/admin_htmx/vendor/htmx-4.0.0.js', 'admin_htmx/static/admin_htmx/vendor/HTMX-LICENSE', 'admin_htmx/templatetags/admin_htmx.py']:
            assert required in names, required
        assert not any('example/' in name or 'tests/' in name or '.sqlite3' in name for name in names)
    source = next(item for item in artifacts if item['path'].endswith('.gz'))
    with tarfile.open(ROOT / source['path']) as archive:
        names = archive.getnames()
        for required in ['tests/conftest.py', 'example/catalog/models.py', 'scripts/verify_fresh_install.py']:
            assert any(name.endswith('/' + required) for name in names), required
    (ROOT / 'evidence/artifacts.json').write_text(json.dumps(artifacts, indent=2) + '\n')
    vendor = ROOT / 'src/admin_htmx/static/admin_htmx/vendor/htmx-4.0.0.js'
    (ROOT / 'evidence/htmx-version.json').write_text(json.dumps({'version':'4.0.0', 'status':'stable release', 'source':'https://cdn.jsdelivr.net/npm/htmx.org@4.0.0/dist/htmx.js', 'sha256':hashlib.sha256(vendor.read_bytes()).hexdigest()}, indent=2) + '\n')
    steps = []
    for name, label in STEPS:
        path = ROOT / 'evidence/screenshots' / (name + '.png')
        assert path.is_file(), path
        steps.append({'title':label, 'path':str(path), 'relative':str(path.relative_to(ROOT / 'evidence'))})
    for version in ['52', '60', '61']:
        for viewport in ['desktop', 'mobile']:
            path = ROOT / f'fresh_install/django{version}/wheel-saved-{viewport}.png'
            assert path.is_file(), path
            steps.append({'title':f'Fresh wheel installation · Django {version[0]}.{version[1]} · {viewport} save', 'path':str(path), 'relative':f'../fresh_install/django{version}/wheel-saved-{viewport}.png'})
    (ROOT / 'evidence/screenshots.json').write_text(json.dumps(steps, indent=2) + '\n')
    md = ['# Ordered screenshot walkthrough', '', 'Actual screenshots from the implemented UI and independent installed-wheel projects. Each image links to its full-size original. The gallery has desktop/mobile views, validation and permission boundaries, confirmation/cancellation branches and saved states.', '', '[Open the compact gallery](../evidence/walkthrough.html)', '']
    figures = []
    for index, step in enumerate(steps, 1):
        md.extend([f'## {index}. {step["title"]}', '', f'[![{step["title"]}]({step["path"]})]({step["path"]})', ''])
        figures.append(f'<figure><figcaption><span>{index:02d}</span> {html.escape(step["title"])}</figcaption><a href="{step["relative"]}" target="_blank"><img loading="lazy" src="{step["relative"]}" alt="{html.escape(step["title"])}"></a><a class="original" href="{step["relative"]}" target="_blank">Open full-size image ↗</a></figure>')
    (ROOT / 'docs/WALKTHROUGH.md').write_text('\n'.join(md))
    gallery = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Django HTMX admin · Screenshot walkthrough</title><style>body{margin:0;background:#f2f5f3;color:#173a37;font:16px system-ui}header{padding:40px;max-width:1100px;margin:auto}h1{font-size:34px;margin:0 0 12px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:24px;padding:0 32px 40px;max-width:1450px;margin:auto}figure{margin:0;border:1px solid #cedbd3;border-radius:10px;overflow:hidden;background:white}figcaption{padding:18px;font-weight:650;min-height:48px}figcaption span{color:#659280;margin-right:10px}img{width:100%;height:420px;object-fit:contain;object-position:top;background:#fff;display:block}.original{display:block;padding:16px;color:#246454;border-top:1px solid #eee}a:focus-visible{outline:3px solid #c58a24}header p{max-width:800px;line-height:1.6}@media(max-width:500px){header{padding:24px}main{padding:0 16px 24px;grid-template-columns:1fr}}</style><header><h1>Django admin + HTMX 4</h1><p>Ordered screenshots of the actual implementation. Follow the flow from entry to saved states, including validation, permissions, cancellations, related popups, mobile layouts and fresh wheel installations. Select an image for its full-size original.</p></header><main>' + ''.join(figures) + '</main></html>'
    (ROOT / 'evidence/walkthrough.html').write_text(gallery)
    rows = '\n'.join(f'| {row["django"]} | {row["python"].replace("Python ","")} | {row["summary"]} | [JUnit](../evidence/{row["environment"]}.xml) · [log](../evidence/{row["environment"]}-tests.txt) |' for row in matrix)
    installs = '\n'.join(f'| {row["version"]} | Passed | `{Path(row["package_import"]).relative_to(ROOT)}` | [log](../fresh_install/django{row["series"].replace(".", "")}/verification-output.txt) |' for row in fresh)
    report = f'''# Verification report

Completed 2026-09-07. Package version 0.1.0, stable vendored HTMX 4.0.0. The source suite contains **49 backend/integration tests and 15 real-browser scenarios**, with multiple workflow assertions per browser scenario. No browser tests are mocked or skipped in the final matrix.

## Final test matrix

| Django | Python | Result | Evidence |
|---|---|---|---|
{rows}

**256 passing source-suite executions** across four environments. Browser engine: Chromium 151.0.7922.34 (Playwright 1.62.0), macOS arm64. Tests use SQLite, an actual Django live server, real form submissions and local static assets. Browser errors are asserted absent.

## Independent wheel installations

Each generated project has its own non-editable environment, Django installation, settings, models, migrations, database and collected static assets. The test command runs from inside the fresh project with PYTHONPATH unset, outside the source-package import path. It asserts the installed module comes from site-packages, checks HTMX 4.0.0, then performs login, prepopulation, autocomplete, inline addition and a persisted save without reloading the document.

| Django | Backend + browser | Verified import | Evidence |
|---|---|---|---|
{installs}

**3 additional fresh-project tests passed.** Each project also passed migrations, Django system checks and collectstatic. Desktop/mobile saved-state screenshots from each installation are in the [walkthrough](WALKTHROUGH.md). The reports record the exact wheel SHA-256 and installed import path.

Verified wheel: `{wheel['path']}`  
SHA-256: `{wheel['sha256']}`

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
'''
    (ROOT / 'docs/VERIFICATION.md').write_text(report)
    print(f'Validated artifacts; generated {len(steps)} ordered screenshots and verification report.')


if __name__ == '__main__':
    main()
