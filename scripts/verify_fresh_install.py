#!/usr/bin/env python3
"""Build and verify the wheel in independent, non-editable Django projects.

Run with a project-local Python 3.12+ and uv installed. Every environment, cache,
project, database, static collection, screenshot and report stays in this repo.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
from check_release import read_version

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "UV_CACHE_DIR": str(ROOT / ".cache/uv"), "TMPDIR": str(ROOT / ".cache/tmp"), "PLAYWRIGHT_BROWSERS_PATH": str(ROOT / ".cache/ms-playwright"), "SOURCE_DATE_EPOCH": "1788825600"}
ENV.pop("PYTHONPATH", None)
ENV.pop("DJANGO_SETTINGS_MODULE", None)
(ROOT / ".cache/tmp").mkdir(parents=True, exist_ok=True)


def run(*args, cwd=ROOT):
    print("+", " ".join(map(str, args)), flush=True)
    result = subprocess.run(list(map(str, args)), cwd=cwd, env=ENV, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
    return result.stdout


MODELS = '''from django.db import models

class Publisher(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self): return self.name

class Publication(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT)
    published_at = models.DateTimeField(null=True, blank=True)
    def __str__(self): return self.title

class Page(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
'''
ADMIN = '''from django.contrib import admin
from .models import Publisher, Publication, Page

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    search_fields = ['name']
    ordering = ['name']

class PageInline(admin.TabularInline):
    model = Page
    extra = 1

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    search_fields = ['title']
    prepopulated_fields = {'slug': ['title']}
    autocomplete_fields = ['publisher']
    inlines = [PageInline]
'''
TESTS = '''import os
from pathlib import Path
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright, expect
from .models import Publisher, Publication
import admin_htmx
import django

class WheelInstallationTests(StaticLiveServerTestCase):
    def test_installed_wheel_backend_and_browser(self):
        installed = Path(admin_htmx.__file__).resolve()
        assert 'site-packages' in str(installed), installed
        assert '/src/' not in str(installed), installed
        get_user_model().objects.create_superuser('freshadmin', 'admin@example.test', 'Fresh-install-2026!')
        Publisher.objects.create(name='Fresh project press')
        self.client.login(username='freshadmin', password='Fresh-install-2026!')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin-htmx-enhanced')
        denied = self.client.post('/admin/library/publication/add/', {})
        self.assertContains(denied, 'errorlist')
        os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
        errors = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            page.on('pageerror', lambda err: errors.append(str(err)))
            page.goto(self.live_server_url + '/admin/')
            page.wait_for_function('window.AdminHTMX && !AdminHTMX.busy')
            assert page.evaluate('htmx.version') == '4.0.0'
            page.evaluate('window.freshMarker = 42')
            page.locator('#id_username').fill('freshadmin')
            page.locator('#id_password').fill('Fresh-install-2026!')
            page.locator('input[type=submit]').click()
            expect(page.locator('h1')).to_contain_text('Site administration')
            page.wait_for_function('!AdminHTMX.busy')
            page.locator('#content-main .model-publication .addlink').click()
            expect(page.locator('#id_title')).to_be_visible()
            page.wait_for_function('!AdminHTMX.busy')
            page.locator('#id_title').fill('Installed from the wheel')
            page.locator('#id_title').press('Tab')
            expect(page.locator('#id_slug')).to_have_value('installed-from-the-wheel')
            page.locator('.select2-selection').click()
            page.locator('.select2-search__field').fill('Fresh')
            page.get_by_role('option', name='Fresh project press', exact=True).click()
            expect(page.locator('.datetimeshortcuts')).to_have_count(2)
            page.locator('#page_set-group .add-row a').click()
            expect(page.locator('#id_page_set-TOTAL_FORMS')).to_have_value('2')
            page.locator('#id_page_set-0-text').fill('Verified in a clean Django project')
            page.locator('[name=_continue]').click()
            page.wait_for_url('**/change/')
            page.wait_for_function('!AdminHTMX.busy')
            expect(page.locator('.messagelist')).to_contain_text('added successfully')
            assert page.evaluate('window.freshMarker') == 42
            shot = Path.cwd() / 'wheel-saved-desktop.png'
            page.screenshot(path=str(shot), full_page=True)
            page.set_viewport_size({'width':390, 'height':844})
            expect(page.locator('link[href*="admin_htmx"]')).to_have_count(0)
            expect(page.locator('#admin-htmx-nav, #admin-htmx-filters')).to_have_count(0)
            page.screenshot(path=str(Path.cwd() / 'wheel-saved-mobile.png'), full_page=True)
            browser.close()
        os.environ.pop('DJANGO_ALLOW_ASYNC_UNSAFE', None)
        publication = Publication.objects.get(slug='installed-from-the-wheel')
        assert publication.page_set.get().text == 'Verified in a clean Django project'
        assert not errors, errors
        print('WHEEL_IMPORT=' + str(installed))
        print('DJANGO_VERSION=' + django.get_version())
        print('HTMX_VERSION=4.0.0')
'''


def verify(series, wheel):
    name = 'django' + series.replace('.', '')
    project = ROOT / 'fresh_install' / name
    project.mkdir(parents=True, exist_ok=True)
    env_dir = ROOT / '.venvs' / ('fresh-' + name)
    if not (env_dir / 'bin/python').exists():
        base = Path(sys._base_executable).resolve()
        run('uv', 'venv', env_dir, '--python', base)
    python = env_dir / 'bin/python'
    run('uv', 'pip', 'install', '--python', python, '--reinstall-package', 'django-admin-htmx', wheel, f'Django=={series}.*', 'playwright>=1.51')
    if not (project / 'manage.py').exists():
        run(python, '-m', 'django', 'startproject', 'verification', project)
        run(python, 'manage.py', 'startapp', 'library', cwd=project)
    (project / 'library/models.py').write_text(MODELS)
    (project / 'library/admin.py').write_text(ADMIN)
    (project / 'library/tests.py').write_text(TESTS)
    settings = project / 'verification/settings.py'
    contents = settings.read_text().split('# BEGIN WHEEL VERIFICATION')[0]
    contents = re.sub(r'^SECRET_KEY = .*$', "SECRET_KEY = 'fresh-install-local-test-only'", contents, flags=re.MULTILINE)
    contents += '''\n# BEGIN WHEEL VERIFICATION
INSTALLED_APPS.insert(0, 'admin_htmx')
INSTALLED_APPS.append('library')
MIDDLEWARE.append('admin_htmx.middleware.AdminHtmxMiddleware')
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
STATIC_ROOT = BASE_DIR / 'staticfiles'
'''
    settings.write_text(contents)
    run(python, 'manage.py', 'makemigrations', 'library', '--noinput', cwd=project)
    run(python, 'manage.py', 'migrate', '--noinput', cwd=project)
    run(python, 'manage.py', 'check', cwd=project)
    static_output = run(python, 'manage.py', 'collectstatic', '--noinput', cwd=project)
    output = run(python, 'manage.py', 'test', 'library', '--noinput', '-v', '2', cwd=project)
    (project / 'verification-output.txt').write_text(output)
    return {'series': series, 'version': output.split('DJANGO_VERSION=')[1].splitlines()[0], 'package_import': output.split('WHEEL_IMPORT=')[1].splitlines()[0], 'wheel': str(wheel.relative_to(ROOT)), 'sha256': hashlib.sha256(wheel.read_bytes()).hexdigest(), 'tests': '1 fresh-project test, backend + real Chromium, passed', 'collectstatic': static_output.strip(), 'project': str(project)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--series', nargs='+', default=['5.2', '6.0', '6.1'])
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--dist-dir', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    if not args.skip_build:
        run('uv', 'build', '--out-dir', args.dist_dir, '--python', sys.executable)
    version = read_version()
    wheel = next(args.dist_dir.resolve().glob(f'django_admin_htmx-{version}-*.whl'))
    results = [verify(series, wheel) for series in args.series]
    (ROOT / 'evidence').mkdir(exist_ok=True)
    (ROOT / 'evidence/fresh-install.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
