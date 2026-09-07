import json
import pytest
from bs4 import BeautifulSoup
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from admin_htmx.checks import check_configuration
from admin_htmx.middleware import ScriptInventory
from example.catalog.models import Author, Book, Chapter, Note
from conftest import book_payload

HX = {"HTTP_HX_REQUEST": "true", "HTTP_X_ADMIN_HTMX": "true"}


@pytest.mark.parametrize("path", ["/admin/", "/admin/catalog/", "/admin/catalog/book/", "/admin/catalog/book/add/", "/admin/password_change/", "/editorial/", "/editorial/catalog/book/"])
@pytest.mark.parametrize("enhanced", [False, True])
def test_pages_preserve_full_document_and_semantics(auth_client, path, enhanced):
    response = auth_client.get(path, **(HX if enhanced else {}))
    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.content
    assert response["X-Admin-HTMX-Page"] == "true"
    soup = BeautifulSoup(response.content, "html.parser")
    assert soup.select_one('meta[name="admin-htmx-enhanced"]')
    assert soup.select_one('form input[name="csrfmiddlewaretoken"]')
    assert all(el.get("type") == "application/json" and not el.get("src") for el in soup.select("[data-admin-htmx-script]"))
    assert "X-Admin-HTMX" in response["Vary"]


@pytest.mark.parametrize("path", ["/admin/", "/admin/catalog/book/", "/editorial/"])
def test_anonymous_redirect_is_hx_location_without_bypassing_auth(client, path):
    response = client.get(path, **HX)
    assert response.status_code == 200
    assert "/login/?next=" in json.loads(response["HX-Location"])["path"]
    normal = client.get(path)
    assert normal.status_code == 302


def test_login_failure_success_logout(client, data):
    bad = client.post("/admin/login/?next=/admin/", {"username": "admin", "password": "wrong"}, **HX)
    assert bad.status_code == 200 and b"errornote" in bad.content
    success = client.post("/admin/login/?next=/admin/", {"username": "admin", "password": "Local-demo-2026!"}, **HX)
    assert json.loads(success["HX-Location"])["path"] == "/admin/"
    assert client.get("/admin/logout/").status_code == 405
    assert client.post("/admin/logout/", **HX).status_code == 200
    assert client.get("/admin/").status_code == 302


def test_password_change(auth_client, data):
    path = "/admin/password_change/"
    bad = auth_client.post(path, {"old_password": "wrong", "new_password1": "Changed-password-2026", "new_password2": "Changed-password-2026"}, **HX)
    assert b"errorlist" in bad.content
    good = auth_client.post(path, {"old_password": "Local-demo-2026!", "new_password1": "Changed-password-2026", "new_password2": "Changed-password-2026"}, **HX)
    assert json.loads(good["HX-Location"])["path"].endswith("password_change/done/")
    data["admin"].refresh_from_db()
    assert data["admin"].check_password("Changed-password-2026")
    assert auth_client.get("/admin/").status_code == 200


@pytest.mark.parametrize("button,suffix", [("_save", "/admin/catalog/book/"), ("_continue", "/change/"), ("_addanother", "/add/")])
def test_save_variants_and_audit_log(auth_client, data, button, suffix):
    payload = book_payload(data["author"])
    payload.pop("_save")
    payload[button] = "Save"
    response = auth_client.post("/admin/catalog/book/add/", payload, **HX)
    assert response.status_code == 200
    assert json.loads(response["HX-Location"])["path"].endswith(suffix)
    book = Book.objects.get(slug="a-new-book")
    assert LogEntry.objects.filter(object_id=str(book.pk), action_flag=1).exists()


@pytest.mark.parametrize("fields", [{"title": "invalid"}, {"price": "-1"}, {"slug": "field-notes"}, {"title": ""}])
def test_validation_preserves_form_and_database(auth_client, data, fields):
    response = auth_client.post("/admin/catalog/book/add/", book_payload(data["author"], **fields), **HX)
    assert response.status_code == 200
    assert b"errorlist" in response.content
    assert "HX-Location" not in response
    assert Book.objects.count() == 1


def test_inlines_upload_and_history(auth_client, data, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    payload = book_payload(data["author"], **{
        "chapter_set-TOTAL_FORMS": "1", "chapter_set-0-title": "Introduction", "chapter_set-0-position": "1",
        "note_set-TOTAL_FORMS": "1", "note_set-0-text": "Proof reviewed",
        "attachment": SimpleUploadedFile("notes.txt", b"local upload evidence"), "tags": [str(data["tag"].pk)],
    })
    response = auth_client.post("/admin/catalog/book/add/", payload, **HX)
    assert "HX-Location" in response
    book = Book.objects.get(slug="a-new-book")
    assert book.chapter_set.get().title == "Introduction"
    assert book.note_set.get().text == "Proof reviewed"
    assert book.tags.get() == data["tag"]
    assert book.attachment.read() == b"local upload evidence"
    history = auth_client.get(f"/admin/catalog/book/{book.pk}/history/", **HX)
    assert b"Added." in history.content


def test_invalid_inline_rolls_back_parent(auth_client, data):
    payload = book_payload(data["author"], **{"chapter_set-TOTAL_FORMS": "1", "chapter_set-0-title": "Invalid chapter", "chapter_set-0-position": "-1"})
    response = auth_client.post("/admin/catalog/book/add/", payload, **HX)
    assert b"errorlist" in response.content
    assert Book.objects.count() == 1 and Chapter.objects.count() == 0


def test_save_as_new_and_preserved_filters(auth_client, data):
    response = auth_client.post(f'/admin/catalog/book/{data["book"].pk}/change/?_changelist_filters=status__exact%3Ddraft', book_payload(data["author"], _saveasnew="Save as new"), **HX)
    assert "HX-Location" in response
    assert Book.objects.count() == 2
    assert "_changelist_filters=" in json.loads(response["HX-Location"])["path"]


@pytest.mark.parametrize("query,expected", [("q=Field", 1), ("q=missing", 0), ("status__exact=draft", 1), ("status__exact=published", 0), ("o=-1", 1), ("_facets=True", 1)])
def test_changelist_queries(auth_client, query, expected):
    response = auth_client.get("/admin/catalog/book/?" + query, **HX)
    assert response.context["cl"].result_count == expected


def test_actions_confirmation_and_download(auth_client, data):
    path = "/admin/catalog/book/"
    selected = {"action": "publish", "_selected_action": [data["book"].pk], "index": "0"}
    response = auth_client.post(path, selected, **HX)
    assert "HX-Location" in response
    data["book"].refresh_from_db()
    assert data["book"].status == "published"
    selected["action"] = "archive"
    confirmation = auth_client.post(path, selected, **HX)
    assert b"Confirm archive" in confirmation.content
    assert "HX-Location" not in confirmation
    selected["confirm_archive"] = "yes"
    response = auth_client.post(path, selected, **HX)
    data["book"].refresh_from_db()
    assert data["book"].status == "archived"
    selected["action"] = "export"
    download = auth_client.post(path, selected, **HX)
    assert download["Content-Disposition"] == 'attachment; filename="books.csv"'
    assert b"Field notes,archived" in download.content


def test_bulk_delete_confirmation(auth_client, data):
    payload = {"action": "delete_selected", "_selected_action": [data["book"].pk], "index": "0"}
    confirm = auth_client.post("/admin/catalog/book/", payload, **HX)
    assert b"Are you sure" in confirm.content and Book.objects.exists()
    payload["post"] = "yes"
    response = auth_client.post("/admin/catalog/book/", payload, **HX)
    assert "HX-Location" in response and not Book.objects.exists()


def test_delete_protected_and_normal(auth_client, data):
    protected = auth_client.get(f'/admin/catalog/author/{data["author"].pk}/delete/', **HX)
    assert b"protected" in protected.content
    auth_client.post(f'/admin/catalog/author/{data["author"].pk}/delete/', {"post": "yes"}, **HX)
    assert Author.objects.exists()
    response = auth_client.post(f'/admin/catalog/book/{data["book"].pk}/delete/', {"post": "yes"}, **HX)
    assert "HX-Location" in response and not Book.objects.exists()


@pytest.mark.parametrize("price,valid", [("24.50", True), ("-4", False)])
def test_list_editable_validation(auth_client, data, price, valid):
    payload = {"form-TOTAL_FORMS": "1", "form-INITIAL_FORMS": "1", "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000", "form-0-id": data["book"].pk, "form-0-status": "published", "form-0-price": price, "_save": "Save"}
    response = auth_client.post("/admin/catalog/book/", payload, **HX)
    data["book"].refresh_from_db()
    assert ("HX-Location" in response) == valid
    assert str(data["book"].price) == ("24.50" if valid else "12.00")


def test_csrf_is_enforced(data):
    client = Client(enforce_csrf_checks=True)
    client.force_login(data["admin"])
    response = client.post("/admin/catalog/book/add/", book_payload(data["author"]), **HX)
    assert response.status_code == 403 and Book.objects.count() == 1
    page = client.get("/admin/catalog/book/add/")
    token = BeautifulSoup(page.content, "html.parser").select_one('[name="csrfmiddlewaretoken"]')["value"]
    response = client.post("/admin/catalog/book/add/", book_payload(data["author"], csrfmiddlewaretoken=token), **HX)
    assert "HX-Location" in response and Book.objects.count() == 2


def test_view_only_and_nonstaff_permissions(client, data):
    user = get_user_model().objects.create_user("viewer", password="test", is_staff=True)
    user.user_permissions.add(Permission.objects.get(codename="view_book"))
    client.force_login(user)
    assert client.get("/admin/catalog/book/", **HX).status_code == 200
    page = client.get(f'/admin/catalog/book/{data["book"].pk}/change/', **HX)
    assert b'name="_save"' not in page.content
    assert client.post(f'/admin/catalog/book/{data["book"].pk}/change/', book_payload(data["author"]), **HX).status_code == 403
    assert client.get("/admin/catalog/book/add/", **HX).status_code == 403
    user.is_staff = False
    user.save()
    assert "HX-Location" in client.get("/admin/", **HX)


def test_autocomplete_permissions_and_popup_protocol(auth_client, client, data):
    url = "/admin/autocomplete/?app_label=catalog&model_name=book&field_name=author&term=Maya"
    response = auth_client.get(url, **HX)
    assert response.json()["results"] == [{"id": str(data["author"].pk), "text": "Maya Rivers"}]
    popup = auth_client.get("/admin/catalog/author/add/?_popup=1")
    assert "X-Admin-HTMX-Page" not in popup
    assert b'data-admin-htmx-script' not in popup.content
    saved = auth_client.post("/admin/catalog/author/add/?_popup=1", {"name": "Popup author", "email": "", "_popup": "1", "_save": "Save"})
    assert b"popup_response.js" in saved.content
    client.logout()
    assert client.get(url).status_code == 302


def test_disabled_and_non_admin_isolation(auth_client):
    with override_settings(ADMIN_HTMX_ENABLED=False):
        assert "X-Admin-HTMX-Page" not in auth_client.get("/admin/", **HX)
    assert auth_client.get("/", **HX).content == b"Fieldwork example site"
    assert "HX-Request" not in auth_client.get("/").get("Vary", "")


def test_custom_media_requires_explicit_lifecycle_optin():
    known = {"stock": {"/static/admin/js/core.js"}, "runtime": set()}
    html = '<html><script src="/static/custom.js"></script></html>'
    assert ScriptInventory(html, known, "/admin/jsi18n/").native
    html = '<script src="/static/custom.js" data-admin-htmx-load="once"></script>'
    result = ScriptInventory(html, known, "/admin/jsi18n/")
    assert not result.native and "data-admin-htmx-src" in result.transformed()


def test_system_check_for_missing_middleware():
    with override_settings(MIDDLEWARE=[]):
        assert "admin_htmx.W002" in [warning.id for warning in check_configuration(None)]


def test_existing_inline_update_delete_and_upload_clear(auth_client, data, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    book = data['book']
    first = Chapter.objects.create(book=book, title='Keep', position=1)
    second = Chapter.objects.create(book=book, title='Remove', position=2)
    book.attachment.save('clear-me.txt', SimpleUploadedFile('clear-me.txt', b'clear attachment'))
    payload = book_payload(data['author'], title=book.title, slug=book.slug, **{
        'chapter_set-TOTAL_FORMS': '2', 'chapter_set-INITIAL_FORMS': '2',
        'chapter_set-0-id': first.pk, 'chapter_set-0-book': book.pk, 'chapter_set-0-title': 'Updated chapter', 'chapter_set-0-position': '3',
        'chapter_set-1-id': second.pk, 'chapter_set-1-book': book.pk, 'chapter_set-1-title': 'Remove', 'chapter_set-1-position': '2', 'chapter_set-1-DELETE': 'on',
        'attachment-clear': 'on',
    })
    response = auth_client.post(f'/admin/catalog/book/{book.pk}/change/', payload, **HX)
    assert 'HX-Location' in response
    assert not Chapter.objects.filter(pk=second.pk).exists()
    first.refresh_from_db()
    assert first.title == 'Updated chapter' and first.position == 3
    book.refresh_from_db()
    assert not book.attachment


def test_escaped_object_content_and_unknown_htmx_clients(auth_client, data):
    book = data['book']
    book.title = '<script>alert("untrusted record")</script>'
    book.save()
    response = auth_client.get('/admin/catalog/book/', **HX)
    assert b'&lt;script&gt;' in response.content
    assert b'<script>alert("untrusted record")</script>' not in response.content
    # This middleware must not hijack a separately configured HTMX integration.
    response = auth_client.post('/admin/catalog/book/add/', book_payload(data['author']), HTTP_HX_REQUEST='true')
    assert response.status_code == 302 and 'HX-Location' not in response


def test_gzip_order_and_compressed_response(auth_client, settings):
    import gzip
    adapter = 'admin_htmx.middleware.AdminHtmxMiddleware'
    gzip_middleware = 'django.middleware.gzip.GZipMiddleware'
    original = list(settings.MIDDLEWARE)
    settings.MIDDLEWARE = [gzip_middleware, *original]
    response = auth_client.get('/admin/', HTTP_ACCEPT_ENCODING='gzip', **HX)
    assert response['Content-Encoding'] == 'gzip'
    assert b'admin-htmx-enhanced' in gzip.decompress(response.content)
    assert response['X-Admin-HTMX-Page'] == 'true'
    settings.MIDDLEWARE = [adapter, gzip_middleware, *[m for m in original if m != adapter]]
    assert 'admin_htmx.W003' in [warning.id for warning in check_configuration(None)]
