import os
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
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(Path.cwd() / 'wheel-saved-mobile.png'), full_page=True)
            browser.close()
        os.environ.pop('DJANGO_ALLOW_ASYNC_UNSAFE', None)
        publication = Publication.objects.get(slug='installed-from-the-wheel')
        assert publication.page_set.get().text == 'Verified in a clean Django project'
        assert not errors, errors
        print('WHEEL_IMPORT=' + str(installed))
        print('DJANGO_VERSION=' + django.get_version())
        print('HTMX_VERSION=4.0.0')
