"""Real Chromium regression tests against Django's live server, not mocked HTML."""
import json
import base64
import os
import re
from pathlib import Path
import pytest
from playwright.sync_api import expect, sync_playwright
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from example.catalog.models import Author, Book, Chapter, Note

pytestmark = [pytest.mark.browser, pytest.mark.django_db(transaction=True)]
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def browser():
    # Playwright sync API runs a private event loop; test ORM calls stay synchronous.
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()
    os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)


@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" and "favicon" not in msg.text and "Failed to load resource" not in msg.text else None)
    page.set_default_timeout(10000)
    yield page
    context.close()
    assert not errors, "Browser errors: " + json.dumps(errors)


def ready(page):
    expect(page.locator('#content-start')).to_have_attribute('aria-busy', 'false')
    expect(page.locator('#admin-htmx-status[data-state="error"]')).to_have_count(0)


def shot(page, name, full=True):
    if os.environ.get("ADMIN_HTMX_SCREENSHOTS") == "1":
        ready(page)
        path = ROOT / "evidence/screenshots" / f"{name}.png"
        page.screenshot(path=str(path), full_page=full)


def login(page, live_server, username="admin", password="Local-demo-2026!"):
    page.goto(live_server.url + "/admin/")
    ready(page)
    page.locator('#id_username').fill(username)
    page.locator('#id_password').fill(password)
    page.locator('input[type=submit]').click()
    expect(page.locator('body')).not_to_have_class(re.compile(r'\blogin\b'))
    expect(page.locator('h1')).to_contain_text('Workspace overview')
    ready(page)


def nav(page, selector, url_part=None):
    page.locator(selector).filter(visible=True).first.click()
    if url_part:
        page.wait_for_url(re.compile(re.escape(url_part) + r'(?:[?#].*)?$'))
    ready(page)


def books(page):
    nav(page, 'a[href="/admin/catalog/book/"]', '/admin/catalog/book/')
    expect(page.locator('#result_list')).to_be_visible()


def add_book(page, title="Browser field guide"):
    nav(page, '.object-tools .addlink', '/admin/catalog/book/add/')
    page.locator('#id_title').fill(title)
    page.locator('#id_title').press('Tab')
    expect(page.locator('#id_slug')).to_have_value(title.lower().replace(' ', '-'))
    page.locator('.select2-selection').click()
    page.locator('.select2-search__field').fill('Maya')
    page.get_by_role('option', name='Maya Rivers', exact=True).click()
    expect(page.locator('#id_author')).not_to_have_value('')


def test_login_validation_dashboard_app_index_history_and_logout(page, live_server, data):
    page.goto(live_server.url + '/admin/')
    ready(page)
    assert page.evaluate('htmx.version') == '4.0.0'
    page.evaluate('window.navigationMarker = "same-document"')
    shot(page, '01-desktop-login')
    page.locator('#id_username').fill('admin')
    page.locator('#id_password').fill('incorrect')
    page.locator('input[type=submit]').click()
    expect(page.locator('.errornote')).to_be_visible()
    ready(page)
    shot(page, '02-login-error')
    page.locator('#id_password').fill('Local-demo-2026!')
    page.locator('input[type=submit]').click()
    expect(page.locator('h1')).to_contain_text('Workspace overview')
    ready(page)
    assert page.evaluate('window.navigationMarker') == 'same-document'
    shot(page, '03-desktop-dashboard')
    nav(page, '#content-main a[href="/admin/catalog/"]', '/admin/catalog/')
    shot(page, '04-app-index')
    books(page)
    shot(page, '05-desktop-changelist')
    page.go_back()
    expect(page.locator('h1')).to_contain_text('Catalog administration')
    ready(page)
    page.go_forward()
    expect(page.locator('#result_list')).to_be_visible()
    ready(page)
    assert page.evaluate('window.navigationMarker') == 'same-document'
    assert page.evaluate("Object.keys(localStorage).filter(k=>/htmx/i.test(k))") == []
    page.locator('#logout-form button').click()
    expect(page.locator('h1')).to_contain_text('Logged out')
    ready(page)
    shot(page, '25-logout')


def test_crud_widgets_inlines_upload_save_variants_history_delete(page, live_server, data):
    login(page, live_server)
    page.evaluate('window.navigationMarker = "same-document"')
    books(page)
    add_book(page)
    expect(page.locator('.datetimeshortcuts')).to_have_count(2)
    page.locator('#calendarlink0').click()
    expect(page.locator('#calendarbox0')).to_be_visible()
    shot(page, '06-add-form-calendar', full=False)
    page.locator('#calendarbox0').get_by_text('Today', exact=True).click()
    page.locator('#id_tags_from').select_option(label='Design')
    page.locator('#id_tags_add').click()
    expect(page.locator('#id_tags_to option')).to_have_text(['Design'])
    page.locator('#chapter_set-group .add-row a').click()
    expect(page.locator('#id_chapter_set-TOTAL_FORMS')).to_have_value('2')
    page.locator('#id_chapter_set-0-title').fill('Introduction')
    page.locator('#id_chapter_set-1-title').fill('Field methods')
    page.locator('#id_chapter_set-1-position').fill('2')
    page.locator('#note_set-group .add-row a').click()
    expect(page.locator('#id_note_set-TOTAL_FORMS')).to_have_value('2')
    page.locator('#id_note_set-0-text').fill('Reviewed on site')
    page.locator('#note_set-group .inline-deletelink').last.click()
    expect(page.locator('#id_note_set-TOTAL_FORMS')).to_have_value('1')
    page.locator('#id_attachment').set_input_files({"name": "field-notes.txt", "mimeType": "text/plain", "buffer": b"fresh browser upload"})
    shot(page, '07-add-form-inlines-upload')
    page.locator('#id_price').fill('-1')
    page.locator('[name=_continue]').click()
    expect(page.locator('.errorlist')).to_be_visible()
    ready(page)
    expect(page.locator('#id_title')).to_have_value('Browser field guide')
    assert page.locator('.errorlist').first.evaluate('(e)=>e===document.activeElement')
    shot(page, '08-validation-feedback')
    page.locator('#id_price').fill('18.50')
    page.locator('#id_attachment').set_input_files({"name": "field-notes.txt", "mimeType": "text/plain", "buffer": b"fresh browser upload"})
    page.locator('[name=_continue]').click()
    page.wait_for_url('**/change/')
    ready(page)
    expect(page.locator('.messagelist')).to_contain_text('successfully')
    shot(page, '09-saved-continue')
    book = Book.objects.get(slug='browser-field-guide')
    assert book.chapter_set.count() == 2
    assert book.note_set.count() == 1
    assert book.tags.get().name == 'Design'
    assert book.attachment.read() == b'fresh browser upload'
    assert page.evaluate('window.navigationMarker') == 'same-document'
    nav(page, '.historylink', '/history/')
    expect(page.locator('#change-history')).to_contain_text('Added')
    shot(page, '10-object-history')
    page.go_back()
    expect(page.locator('#id_title')).to_be_visible()
    ready(page)
    page.locator('#id_title').fill('Browser field guide revised')
    page.locator('[name=_save]').click()
    page.wait_for_url('**/admin/catalog/book/')
    ready(page)
    expect(page.locator('.messagelist')).to_contain_text('changed successfully')
    nav(page, f'#result_list a[href="/admin/catalog/book/{book.pk}/change/"]')
    nav(page, '.submit-row .deletelink', '/delete/')
    shot(page, '11-delete-confirmation')
    page.get_by_role('button', name=re.compile(r"Yes, I[’']m sure")).click()
    page.wait_for_url('**/admin/catalog/book/')
    ready(page)
    assert not Book.objects.filter(pk=book.pk).exists()
    shot(page, '12-delete-finished')


def test_search_filters_sort_pagination_list_editing_actions_and_download(page, live_server, data):
    for i in range(11):
        Book.objects.create(title=f'Notebook {i:02d}', slug=f'notebook-{i}', author=data['author'])
    login(page, live_server)
    books(page)
    nav(page, '.paginator a[href*="p=2"]')
    assert 'p=2' in page.url
    nav(page, '#result_list .column-title a')
    assert 'o=' in page.url
    page.locator('#searchbar').fill('Notebook')
    page.locator('#changelist-search input[type=submit]').click()
    page.wait_for_url('**q=Notebook**')
    ready(page)
    expect(page.locator('#result_list tbody tr')).to_have_count(5)
    nav(page, '#changelist-filter a[href*="status__exact=draft"]')
    assert 'status__exact=draft' in page.url
    shot(page, '13-search-filter-sort')
    nav(page, '#changelist-filter a[href*="_facets=True"]')
    expect(page.locator('#changelist-filter')).to_contain_text('Draft (')
    page.locator('[name=form-0-price]').fill('32.50')
    page.locator('[name=_save]').click()
    expect(page.locator('.messagelist')).to_contain_text('changed successfully')
    ready(page)
    shot(page, '14-list-edit-saved')
    page.locator('.action-select').first.check()
    page.locator('[name=action]').select_option('archive')
    page.locator('[name=index]').click()
    expect(page.locator('h1')).to_contain_text('Confirm archive')
    ready(page)
    shot(page, '15-bulk-action-confirmation')
    page.get_by_role('button', name='Confirm archive').click()
    expect(page.locator('.messagelist')).to_contain_text('Archived 1 books')
    ready(page)
    shot(page, '16-bulk-action-finished')
    page.locator('.action-select').first.check()
    page.locator('[name=action]').select_option('export')
    with page.expect_download() as download:
        page.locator('[name=index]').click()
    assert download.value.suggested_filename == 'books.csv'
    ready(page)
    assert b'title,status' in Path(download.value.path()).read_bytes()
    if os.environ.get('ADMIN_HTMX_SCREENSHOTS') == '1': download.value.save_as(str(ROOT / 'evidence/books-export.csv'))
    page.locator('[name=action]').select_option('delete_selected')
    page.locator('[name=index]').click()
    expect(page.locator('h1')).to_contain_text('Delete multiple objects')
    ready(page)
    shot(page, '17-bulk-delete-confirmation')
    page.get_by_role('button', name=re.compile(r"Yes, I[’']m sure")).click()
    expect(page.locator('.messagelist')).to_contain_text('Successfully deleted')
    ready(page)
    shot(page, '41-bulk-delete-finished')


def test_related_popups_autocomplete_and_protection(page, live_server, data):
    login(page, live_server)
    books(page)
    add_book(page, 'Related record guide')
    with page.expect_popup() as opened:
        page.locator('#add_id_author').click()
    popup = opened.value
    expect(popup.locator('#id_name')).to_be_visible()
    popup.locator('#id_name').fill('Popup writer')
    shot_path = ROOT / 'evidence/screenshots/18-related-author-popup.png'
    if os.environ.get('ADMIN_HTMX_SCREENSHOTS') == '1': popup.screenshot(path=str(shot_path), full_page=True)
    with popup.expect_event('close'):
        popup.locator('[name=_save]').click()
    expect(page.locator('#select2-id_author-container')).to_contain_text('Popup writer')
    with page.expect_popup() as lookup:
        page.locator('#lookup_id_reviewer').click()
    popup = lookup.value
    with popup.expect_event('close'):
        popup.locator('#result_list a').filter(has_text='Maya Rivers').click()
    expect(page.locator('#id_reviewer')).to_have_value(str(data['author'].pk))
    shot(page, '19-related-records-selected', full=False)
    # Normal dropdown related change/delete support is exercised via Edition.
    page.goto(live_server.url + '/admin/catalog/edition/add/')
    ready(page)
    page.locator('#id_name').fill('First edition')
    page.locator('#id_book').select_option(str(data['book'].pk))
    with page.expect_popup() as changed:
        page.locator('#change_id_book').click()
    popup = changed.value
    expect(popup.locator('#id_title')).to_be_visible()
    popup.locator('#id_title').fill('Field notes revised')
    with popup.expect_event('close'):
        popup.locator('[name=_save]').click()
    expect(page.locator('#id_book option:checked')).to_contain_text('Field notes revised')
    page.goto(live_server.url + f'/admin/catalog/author/{data["author"].pk}/delete/')
    ready(page)
    expect(page.locator('#content')).to_contain_text('protected')
    shot(page, '20-protected-deletion')


def test_repeated_widgets_save_another_save_as_and_keyboard(page, live_server, data):
    login(page, live_server)
    books(page)
    counts = []
    for i in range(3):
        add_book(page, f'Repeat {i}')
        expect(page.locator('.select2-container')).to_have_count(1)
        expect(page.locator('.datetimeshortcuts')).to_have_count(2)
        expect(page.locator('.add-row')).to_have_count(2)
        counts.append(page.evaluate('AdminHTMX.listenerCount'))
        books(page)
    assert max(counts) == min(counts), counts
    add_book(page, 'Another guide')
    page.locator('[name=_addanother]').click()
    expect(page.locator('.messagelist')).to_contain_text('You may add another')
    ready(page)
    expect(page.locator('#id_title')).to_have_value('')
    books(page)
    book = Book.objects.get(slug='another-guide')
    nav(page, f'#result_list a[href="/admin/catalog/book/{book.pk}/change/"]')
    page.locator('#id_title').fill('Copied guide')
    page.locator('#id_slug').fill('copied-guide')
    page.locator('[name=_saveasnew]').click()
    expect(page.locator('.messagelist')).to_contain_text('added successfully')
    ready(page)
    assert Book.objects.filter(slug='another-guide').exists()
    assert Book.objects.filter(slug='copied-guide').exists()


def test_mobile_navigation_filters_forms_and_password_change(page, live_server, data):
    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(live_server.url + '/admin/')
    ready(page)
    shot(page, '21-mobile-login')
    login(page, live_server)
    shot(page, '22-mobile-dashboard')
    books(page)
    expect(page.locator('#admin-htmx-nav, #admin-htmx-filters')).to_have_count(0)
    expect(page.locator('#nav-sidebar')).to_be_hidden()
    shot(page, '23-mobile-list')
    nav(page, '.breadcrumbs a[href="/admin/catalog/"]')
    shot(page, '24-mobile-navigation', full=False)
    books(page)
    expect(page.locator('#changelist-filter')).to_be_visible()
    shot(page, '26-mobile-filters')
    nav(page, '#changelist-filter a[href*="status__exact=draft"]')
    add_book(page, 'Mobile guide')
    shot(page, '27-mobile-add-form')
    page.locator('[name=_save]').click()
    expect(page.locator('.messagelist')).to_contain_text('added successfully')
    ready(page)
    shot(page, '28-mobile-saved')
    nav(page, '#user-tools a[href="/admin/password_change/"]')
    page.locator('#id_old_password').fill('wrong')
    page.locator('#id_new_password1').fill('Changed-demo-2026!')
    page.locator('#id_new_password2').fill('Changed-demo-2026!')
    page.locator('input[type=submit]').click()
    expect(page.locator('.errorlist')).to_be_visible()
    ready(page)
    shot(page, '29-mobile-password-error')
    page.locator('#id_old_password').fill('Local-demo-2026!')
    page.locator('#id_new_password1').fill('Changed-demo-2026!')
    page.locator('#id_new_password2').fill('Changed-demo-2026!')
    page.locator('input[type=submit]').click()
    page.wait_for_url('**/password_change/done/')
    ready(page)
    shot(page, '30-mobile-password-done')


def test_loading_failure_recovery_and_custom_site(page, live_server, data):
    login(page, live_server)
    books(page)
    add_book(page, 'Retained draft')
    page.route('**/admin/catalog/book/add/', lambda route: route.fulfill(status=500, content_type='text/html', body='Unavailable'))
    page.locator('[name=_save]').click()
    expect(page.locator('#admin-htmx-status')).to_contain_text('Your entries are still here')
    expect(page.locator('#id_title')).to_have_value('Retained draft')
    shot_path = ROOT / 'evidence/screenshots/31-request-error-retained.png'
    if os.environ.get('ADMIN_HTMX_SCREENSHOTS') == '1': page.screenshot(path=str(shot_path), full_page=False)
    page.unroute('**/admin/catalog/book/add/')
    page.locator('[name=_save]').click()
    expect(page.locator('.messagelist')).to_contain_text('added successfully')
    ready(page)
    shot(page, '44-request-error-recovered')
    page.goto(live_server.url + '/editorial/')
    ready(page)
    expect(page.locator('#site-name')).to_contain_text('Editorial')
    page.evaluate('window.siteMarker=1')
    nav(page, '#content-main .model-book th a')
    assert page.evaluate('window.siteMarker') == 1
    shot(page, '32-custom-admin-site')


def test_no_javascript_native_crud(browser, live_server, data):
    context = browser.new_context(java_script_enabled=False)
    page = context.new_page()
    page.goto(live_server.url + '/admin/')
    page.locator('#id_username').fill('admin')
    page.locator('#id_password').fill('Local-demo-2026!')
    page.locator('input[type=submit]').click()
    page.goto(live_server.url + '/admin/catalog/author/add/')
    page.locator('#id_name').fill('No JavaScript author')
    page.locator('[name=_save]').click()
    expect(page.locator('.messagelist')).to_contain_text('added successfully')
    if os.environ.get('ADMIN_HTMX_SCREENSHOTS') == '1': page.screenshot(path=str(ROOT / 'evidence/screenshots/43-no-javascript-saved.png'), full_page=True)
    author = Author.objects.get(name='No JavaScript author')
    page.goto(live_server.url + f'/admin/catalog/author/{author.pk}/delete/')
    page.get_by_role('button', name=re.compile(r"Yes, I[’']m sure")).click()
    assert not Author.objects.filter(pk=author.pk).exists()
    context.close()


def test_busy_state_drops_duplicate_submissions(page, live_server, data):
    login(page, live_server)
    books(page)
    add_book(page, 'One submission only')
    pending = []
    page.route('**/admin/catalog/book/add/', lambda route: pending.append(route))
    page.locator('[name=_save]').click()
    expect(page.locator('#content-start')).to_have_attribute('aria-busy', 'true')
    expect(page.locator('#admin-htmx-status')).to_contain_text('Loading')
    if os.environ.get('ADMIN_HTMX_SCREENSHOTS') == '1':
        page.screenshot(path=str(ROOT / 'evidence/screenshots/33-loading-feedback.png'), full_page=False)
    expect(page.locator('[name=_save]')).to_be_disabled()
    expect(page.locator('#admin-htmx-status')).to_have_class('visually-hidden')
    page.locator('#book_form').dispatch_event('submit')
    assert len(pending) == 1
    pending[0].continue_()
    page.unroute('**/admin/catalog/book/add/')
    expect(page.locator('.messagelist')).to_contain_text('added successfully')
    ready(page)
    assert Book.objects.filter(slug='one-submission-only').count() == 1


def test_view_only_session_expiry_and_user_group_admin(page, live_server, data):
    user = get_user_model().objects.create_user('viewer', password='Local-demo-2026!', is_staff=True)
    user.user_permissions.add(Permission.objects.get(codename='view_book'))
    login(page, live_server, 'viewer')
    books(page)
    expect(page.locator('.object-tools .addlink')).to_have_count(0)
    nav(page, f'#result_list a[href="/admin/catalog/book/{data["book"].pk}/change/"]')
    expect(page.locator('[name=_save]')).to_have_count(0)
    shot(page, '34-view-only-permissions')
    page.context.clear_cookies()
    nav(page, '.breadcrumbs a[href="/admin/catalog/book/"]')
    expect(page.locator('#id_username')).to_be_visible()
    ready(page)
    expect(page.locator('[name=next]')).to_have_value('/admin/catalog/book/')
    shot(page, '42-session-expiry-login')
    page.locator('#id_username').fill('admin')
    page.locator('#id_password').fill('Local-demo-2026!')
    page.locator('input[type=submit]').click()
    expect(page.locator('#result_list')).to_be_visible()
    ready(page)
    page.goto(live_server.url + '/admin/auth/group/add/')
    ready(page)
    expect(page.locator('#id_permissions_from')).to_be_visible()
    page.locator('#id_name').fill('Editors')
    page.locator('#id_permissions_input').fill('Can view book')
    page.locator('#id_permissions_from').select_option(label='Catalog | book | Can view book')
    page.locator('#id_permissions_add').click()
    page.locator('[name=_save]').click()
    expect(page.locator('.messagelist')).to_contain_text('added successfully')
    ready(page)
    page.goto(live_server.url + f'/admin/auth/user/{data["admin"].pk}/change/')
    ready(page)
    expect(page.locator('#id_groups_from')).to_be_visible()
    expect(page.locator('#id_user_permissions_from')).to_be_visible()
    shot(page, '35-user-permission-widgets')


def test_popup_delete_and_single_delete_cancel(page, live_server, data):
    disposable = Author.objects.create(name='Disposable author')
    login(page, live_server)
    books(page)
    add_book(page, 'Popup deletion guide')
    page.locator('.select2-selection').click()
    page.locator('.select2-search__field').fill('Disposable')
    page.get_by_role('option', name='Disposable author', exact=True).click()
    with page.expect_popup() as opened:
        page.locator('#delete_id_author').click()
    popup = opened.value
    expect(popup.locator('#content')).to_contain_text('Are you sure')
    if os.environ.get('ADMIN_HTMX_SCREENSHOTS') == '1': popup.screenshot(path=str(ROOT / 'evidence/screenshots/39-popup-delete-confirmation.png'), full_page=True)
    with popup.expect_event('close'):
        popup.get_by_role('button', name=re.compile(r"Yes, I[’']m sure")).click()
    expect(page.locator(f'#id_author option[value="{disposable.pk}"]')).to_have_count(0)
    assert not Author.objects.filter(pk=disposable.pk).exists()
    shot(page, '40-popup-delete-finished', full=False)
    page.goto(live_server.url + f'/admin/catalog/book/{data["book"].pk}/change/')
    ready(page)
    nav(page, '.submit-row .deletelink')
    page.locator('.cancel-link').click()
    expect(page.locator('#id_title')).to_be_visible()
    ready(page)
    assert Book.objects.filter(pk=data['book'].pk).exists()
    shot(page, '38-delete-cancelled')


def test_list_validation_select_across_and_date_hierarchy(page, live_server, data):
    for i in range(7):
        Book.objects.create(title=f'Selected {i}', slug=f'selected-{i}', author=data['author'])
    login(page, live_server)
    books(page)
    page.locator('[name=form-0-price]').fill('-5')
    page.locator('[name=_save]').click()
    expect(page.locator('.errorlist')).to_be_visible()
    ready(page)
    shot(page, '36-list-validation')
    page.locator('[name=form-0-price]').fill('20')
    page.locator('[name=_save]').click()
    expect(page.locator('.messagelist')).to_contain_text('changed successfully')
    ready(page)
    page.locator('#action-toggle').check()
    page.locator('.actions .question a').click()
    expect(page.locator('[name=select_across]')).to_have_value('1')
    page.locator('[name=action]').select_option('publish')
    page.locator('[name=index]').click()
    expect(page.locator('.messagelist')).to_contain_text('Published 8 books')
    ready(page)
    assert Book.objects.filter(status='published').count() == 8
    nav(page, '.toplinks a[href*="published_at__year"]')
    assert 'published_at__year=' in page.url
    ready(page)


def test_custom_media_native_fallback_and_explicit_lifecycle(page, live_server, data):
    login(page, live_server)
    page.goto(live_server.url + '/editorial/report/?native=1')
    expect(page.locator('#report-status')).to_have_text('Report ready')
    expect(page.locator('meta[name="admin-htmx-enhanced"]')).to_have_count(0)
    page.evaluate('window.customMarker=1')
    page.get_by_role('link', name='Browse books').click()
    expect(page.locator('#result_list')).to_be_visible()
    ready(page)
    assert page.evaluate('window.customMarker') is None
    page.goto(live_server.url + '/editorial/report/')
    ready(page)
    expect(page.locator('#report-status')).to_have_text('Report ready')
    assert page.evaluate('window.reportScriptLoads') == 1
    page.evaluate('window.customMarker=1')
    page.get_by_role('link', name='Browse books').click()
    expect(page.locator('#result_list')).to_be_visible()
    ready(page)
    assert page.evaluate('window.customMarker') == 1
    page.go_back()
    expect(page.locator('#report-status')).to_have_text('Report ready')
    ready(page)
    assert page.evaluate('window.reportScriptLoads') == 1
    shot(page, '37-custom-media-lifecycle')


def test_nonce_policy_survives_htmx_navigation(page, live_server, data):
    login(page, live_server)
    page.goto(live_server.url + '/editorial/report/?csp=1')
    ready(page)
    expect(page.locator('#report-status')).to_have_text('Report ready')
    page.evaluate('window.cspMarker = 1')
    page.get_by_role('link', name='Browse books').click()
    expect(page.locator('#result_list')).to_be_visible()
    ready(page)
    nav(page, '.object-tools .addlink')
    expect(page.locator('.select2-container')).to_have_count(1)
    expect(page.locator('.datetimeshortcuts')).to_have_count(2)
    assert page.evaluate('window.cspMarker') == 1
    page.locator('#id_title').fill('Nonce protected guide')
    page.locator('#id_title').press('Tab')
    expect(page.locator('#id_slug')).to_have_value('nonce-protected-guide')


def test_user_creation_and_admin_password_reset(page, live_server, data):
    login(page, live_server)
    page.goto(live_server.url + '/admin/auth/user/')
    ready(page)
    nav(page, '.object-tools .addlink')
    page.locator('#id_username').fill('new-editor')
    page.locator('#id_password1').fill('Editor-password-2026!')
    page.locator('#id_password2').fill('Editor-password-2026!')
    page.locator('[name=_save]').click()
    expect(page.locator('.messagelist')).to_contain_text('added successfully')
    ready(page)
    shot(page, '45-user-created')
    user = get_user_model().objects.get(username='new-editor')
    assert user.check_password('Editor-password-2026!')
    page.locator('.field-password a').click()
    expect(page.locator('#id_password1')).to_be_visible()
    ready(page)
    page.locator('#id_password1').fill('Reset-password-2026!')
    page.locator('#id_password2').fill('Reset-password-2026!')
    page.locator('[name=set-password]').click()
    expect(page.locator('.messagelist')).to_contain_text('Password changed successfully')
    ready(page)
    user.refresh_from_db()
    assert user.check_password('Reset-password-2026!')
    shot(page, '46-admin-password-reset')


@pytest.mark.parametrize('viewport', [{'width': 1440, 'height': 1000}, {'width': 390, 'height': 844}], ids=['desktop', 'mobile'])
@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_matches_unmodified_django_appearance(page, live_server, data, settings, viewport, theme):
    """Compare actual pixels against Django's own base template, without this app."""
    import copy
    import django
    from django.test import override_settings

    def settle_for_comparison(target):
        target.mouse.move(0, 0)
        target.evaluate('''async () => {
            document.activeElement.blur();
            window.scrollTo(0, 0);
            await document.fonts.ready;
            // Blurring a control can start Django's background-color transition.
            // Compare its final state on both pages, not an intermediate frame.
            await Promise.all(document.getAnimations().filter(animation =>
                animation.effect.getComputedTiming().iterations !== Infinity
            ).map(animation => animation.finished.catch(() => {})));
        }''')

    page.set_viewport_size(viewport)
    page.context.add_init_script(f'localStorage.setItem("theme", {json.dumps(theme)})')
    native = page.context.new_page()
    native.set_viewport_size(viewport)
    templates = copy.deepcopy(settings.TEMPLATES)
    templates[0]['APP_DIRS'] = False
    templates[0]['OPTIONS']['loaders'] = [
        ('django.template.loaders.locmem.Loader', {
            'admin/base.html': (Path(django.__file__).parent / 'contrib/admin/templates/admin/base.html').read_text(),
        }),
        'django.template.loaders.app_directories.Loader',
    ]
    style_profile = """() => [...document.querySelectorAll('#header, #content, h1, .module, .form-row, .submit-row, #changelist-filter, #nav-sidebar, input:not([type=hidden]), select, textarea, button, .results')].filter(el => el.checkVisibility({checkVisibilityCSS: true}) && (!el.closest('details:not([open])') || el.closest('summary'))).map(el => {
        const style = getComputedStyle(el);
        const properties = ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'color', 'backgroundColor', 'padding', 'margin', 'borderRadius', 'borderWidth', 'borderColor', 'boxShadow', 'position', 'display', 'visibility', 'width', 'height'];
        return {tag: el.tagName, id: el.id, styles: properties.map(key => [key, style[key]]), bounds: el.getBoundingClientRect().toJSON()};
    })"""
    records = []
    directory = ROOT / 'evidence/style-parity' / django.get_version()
    directory.mkdir(parents=True, exist_ok=True)
    variant = f'{viewport["width"]}-{theme}'
    marker = 'htmx-kept-this-document'
    paths = [
        ('login', '/admin/login/?next=/admin/'),
        ('dashboard', '/admin/'),
        ('app-index', '/admin/catalog/'),
        ('changelist', '/admin/catalog/book/'),
        ('change-form', f'/admin/catalog/book/{data["book"].pk}/change/'),
        ('history', f'/admin/catalog/book/{data["book"].pk}/history/'),
        ('delete', f'/admin/catalog/book/{data["book"].pk}/delete/'),
        ('password', '/admin/password_change/'),
        ('return-to-list', '/admin/catalog/book/'),
    ]
    for index, (name, path) in enumerate(paths):
        with override_settings(ADMIN_HTMX_ENABLED=False, TEMPLATES=templates):
            native.goto(live_server.url + path)
            native.wait_for_load_state('networkidle')
            expect(native.locator('script[src*="admin_htmx"]')).to_have_count(0)
            settle_for_comparison(native)
            original = native.screenshot(full_page=True, animations='disabled')
            native_styles = native.evaluate(style_profile)
            sheets = native.locator('head link[rel=stylesheet]').evaluate_all('(els) => els.map(el => el.getAttribute("href"))')
        if index == 0:
            page.goto(live_server.url + path)
        elif index > 1:
            with page.expect_request(lambda request: request.url == live_server.url + path and request.headers.get('x-admin-htmx') == 'true') as request:
                page.evaluate('''async path => await htmx.ajax('GET', path, {
                    target: 'body', select: 'body', swap: 'outerSync', push: 'true',
                    headers: {'X-Admin-HTMX': 'true'}
                })''', path)
            assert not request.value.is_navigation_request()
        ready(page)
        page.wait_for_load_state('networkidle')
        expect(page.locator('link[href*="admin_htmx"], #admin-htmx-nav, #admin-htmx-filters')).to_have_count(0)
        assert page.locator('head link[rel=stylesheet]').evaluate_all('(els) => els.map(el => el.getAttribute("href"))') == sheets
        settle_for_comparison(page)
        enhanced_styles = page.evaluate(style_profile)
        assert enhanced_styles == native_styles, f'{name}: computed styles or layout differ: ' + repr(next(((a, b) for a, b in zip(native_styles, enhanced_styles) if a != b), (len(native_styles), len(enhanced_styles))))
        enhanced = page.screenshot(full_page=True, animations='disabled')
        stem = f'{variant}-{name}'
        if os.environ.get('ADMIN_HTMX_SCREENSHOTS') == '1' or original != enhanced:
            (directory / f'{stem}-native.png').write_bytes(original)
            (directory / f'{stem}-htmx.png').write_bytes(enhanced)
        difference = {'changed_pixels': 0, 'max_channel_delta': 0, 'same_dimensions': True}
        if original != enhanced:
            difference = page.evaluate("""async urls => {
                const images = await Promise.all(urls.map(async src => {
                    const image = new Image(); image.src = src; await image.decode(); return image;
                }));
                if (images[0].width !== images[1].width || images[0].height !== images[1].height) return {same_dimensions: false};
                const canvas = new OffscreenCanvas(images[0].width, images[0].height);
                const ctx = canvas.getContext('2d');
                const pixels = images.map(image => {
                    ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.drawImage(image, 0, 0);
                    return ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                });
                let changed = 0, maximum = 0;
                for (let i = 0; i < pixels[0].length; i += 4) {
                    let delta = 0;
                    for (let c = 0; c < 4; c++) delta = Math.max(delta, Math.abs(pixels[0][i+c] - pixels[1][i+c]));
                    if (delta) changed++;
                    maximum = Math.max(maximum, delta);
                }
                return {same_dimensions: true, changed_pixels: changed, max_channel_delta: maximum};
            }""", ['data:image/png;base64,' + base64.b64encode(image).decode() for image in (original, enhanced)])
        # Native control corners vary slightly between rendering passes (Linux
        # Chromium exhibited 5–9 pixels with channel deltas up to 11/255).
        # Keep the pixel budget tiny; styles and geometry must still match exactly.
        matches = difference['same_dimensions'] and difference['max_channel_delta'] <= 16 and difference['changed_pixels'] <= 100
        records.append({'page': name, 'viewport': viewport, 'theme': theme, 'matches_default': matches, **difference})
        (directory / f'{variant}.json').write_text(json.dumps(records, indent=2) + '\n')
        assert matches, f'{stem}: {difference}; see {directory}'
        if index == 0:
            page.evaluate(f'window.styleMarker = {json.dumps(marker)}')
            page.locator('#id_username').fill('admin')
            page.locator('#id_password').fill('Local-demo-2026!')
            page.locator('input[type=submit]').click()
            expect(page.locator('h1')).to_contain_text('Workspace overview')
            ready(page)
        assert page.evaluate('window.styleMarker') == marker
    native.close()
