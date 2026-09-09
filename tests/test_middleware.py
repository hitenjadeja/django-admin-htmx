"""Transport and script-inventory boundaries without database or browser setup."""

import json

import pytest
from bs4 import BeautifulSoup
from django.http import HttpResponse, StreamingHttpResponse
from django.urls import resolve

from admin_htmx.middleware import AdminHtmxMiddleware, ScriptInventory

HX = {"HTTP_HX_REQUEST": "true", "HTTP_X_ADMIN_HTMX": "true"}
HTML = (
    '<html><head><meta name="admin-htmx-root" content="/admin/">'
    '<script src="/static/admin/js/core.js"></script></head><body>Admin</body></html>'
)


def admin_request(rf, path="/admin/", **headers):
    request = rf.get(path, **headers)
    request.resolver_match = resolve(request.path)
    return request


@pytest.mark.parametrize("status", [301, 302, 303])
@pytest.mark.parametrize("with_length", [False, True])
@pytest.mark.parametrize(
    "location,header",
    [
        ("/admin/login/?next=/admin/", "HX-Location"),
        ("login/", "HX-Location"),
        ("http://testserver/editorial/", "HX-Location"),
        ("https://example.test/admin/", "HX-Redirect"),
        ("//example.test/admin/", "HX-Redirect"),
        ("https://testserver/admin/", "HX-Redirect"),
        ("/", "HX-Redirect"),
        ("/missing-route/", "HX-Redirect"),
    ],
)
def test_redirect_destination_and_response_metadata(
    rf, status, with_length, location, header
):
    request = admin_request(rf, **HX)
    response = HttpResponse(
        b"redirect body", status=status, headers={"Location": location}
    )
    response.set_cookie("transport-test", "preserved", httponly=True)
    response["X-Frame-Options"] = "DENY"
    response["Vary"] = "Cookie"
    if with_length:
        response["Content-Length"] = len(response.content)

    result = AdminHtmxMiddleware(lambda request: response)(request)

    assert result is response
    assert result.status_code == 200 and result.content == b""
    assert "Location" not in result
    if header == "HX-Location":
        assert json.loads(result[header]) == {
            "path": location,
            "target": "body",
            "select": "body",
            "swap": "outerSync",
            "headers": {"X-Admin-HTMX": "true"},
        }
        assert "HX-Redirect" not in result
    else:
        assert result[header] == location
        assert "HX-Location" not in result
    assert result.cookies["transport-test"].value == "preserved"
    assert result.cookies["transport-test"]["httponly"]
    assert result["X-Frame-Options"] == "DENY"
    assert set(result["Vary"].split(", ")) == {"Cookie", "HX-Request", "X-Admin-HTMX"}
    assert result.get("Content-Length") == ("0" if with_length else None)


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"HTTP_HX_REQUEST": "true"},
        {"HTTP_X_ADMIN_HTMX": "true"},
        {"HTTP_HX_REQUEST": "false", "HTTP_X_ADMIN_HTMX": "true"},
    ],
)
def test_redirect_requires_both_adapter_headers(rf, headers):
    response = HttpResponse(status=302, headers={"Location": "/admin/"})
    result = AdminHtmxMiddleware(lambda request: response)(admin_request(rf, **headers))
    assert result.status_code == 302 and result["Location"] == "/admin/"
    assert "HX-Location" not in result and "HX-Redirect" not in result


@pytest.mark.parametrize("status", [204, 304, 307, 308, 403, 404, 500])
def test_other_statuses_are_not_rewritten(rf, status):
    response = HttpResponse(HTML, status=status, headers={"Location": "/admin/"})
    result = AdminHtmxMiddleware(lambda request: response)(admin_request(rf, **HX))
    assert result.status_code == status and result.content == HTML.encode()
    assert result["Location"] == "/admin/"
    assert "X-Admin-HTMX-Page" not in result and "HX-Location" not in result


@pytest.mark.parametrize(
    "headers",
    [{"Content-Type": "application/json"}, {"Content-Encoding": "gzip"}],
)
def test_non_html_and_already_encoded_responses_are_untouched(rf, headers):
    response = HttpResponse(HTML, headers=headers)
    result = AdminHtmxMiddleware(lambda request: response)(admin_request(rf, **HX))
    assert result.content == HTML.encode()
    assert "X-Admin-HTMX-Page" not in result


def test_streaming_response_is_not_consumed(rf):
    consumed = []

    def stream():
        consumed.append(True)
        yield HTML.encode()

    response = StreamingHttpResponse(stream())
    result = AdminHtmxMiddleware(lambda request: response)(admin_request(rf, **HX))
    assert result is response and not consumed
    assert "X-Admin-HTMX-Page" not in result
    assert b"".join(result.streaming_content) == HTML.encode()


@pytest.mark.parametrize("path", ["/", "/unresolved/"])
def test_non_admin_and_unresolved_requests_are_untouched(rf, path):
    request = rf.get(path, **HX)
    if path == "/":
        request.resolver_match = resolve(path)
    response = HttpResponse(HTML)
    result = AdminHtmxMiddleware(lambda request: response)(request)
    assert result.content == HTML.encode() and "Vary" not in result


@pytest.mark.parametrize("method", ["get", "post"])
def test_popup_documents_remain_native(rf, method):
    request = getattr(rf, method)("/admin/", {"_popup": "1"}, **HX)
    request.resolver_match = resolve(request.path)
    result = AdminHtmxMiddleware(lambda request: HttpResponse(HTML))(request)
    assert result.content == HTML.encode() and "X-Admin-HTMX-Page" not in result


def test_document_without_integration_marker_remains_native(rf):
    html = '<html><head><script src="/static/admin/js/core.js"></script></head></html>'
    result = AdminHtmxMiddleware(lambda request: HttpResponse(html))(
        admin_request(rf, **HX)
    )
    assert result.content == html.encode() and "X-Admin-HTMX-Page" not in result


def test_unknown_script_preserves_whole_document(rf):
    html = HTML.replace("</head>", '<script src="/custom.js"></script></head>')
    result = AdminHtmxMiddleware(lambda request: HttpResponse(html))(
        admin_request(rf, **HX)
    )
    assert result.content == html.encode()
    assert result["X-Admin-HTMX-Native"] == "true"
    assert "X-Admin-HTMX-Page" not in result


def test_transformed_content_length_counts_encoded_bytes(rf):
    html = HTML.replace("Admin</body>", "Café 日本語</body>")
    response = HttpResponse(html, headers={"Content-Length": "1"})
    result = AdminHtmxMiddleware(lambda request: response)(admin_request(rf, **HX))
    assert result["X-Admin-HTMX-Page"] == "true"
    assert int(result["Content-Length"]) == len(result.content)
    assert "Café 日本語" in result.content.decode(result.charset)
    assert b'content="true"></head>' in result.content


@pytest.mark.parametrize("mode", ["once", "page"])
def test_script_descriptors_preserve_content_and_safe_attributes(mode):
    html = (
        '<main data-label="untouched &amp; exact">Text</main>\n'
        '<script src="/runtime.js"></script>\n'
        '<script type="application/ld+json">{"name": "record"}</script>\n'
        f'<script src="/custom.js?a=1&amp;b=2" type="module" defer async '
        f'data-admin-htmx-load="{mode}" nonce="a&amp;b" crossorigin>'
        'window.example = "kept";</script>\n'
        '<script src="/admin/jsi18n/"></script>'
    )
    inventory = ScriptInventory(
        html, {"runtime": {"/runtime.js"}, "stock": set()}, "/admin/jsi18n/"
    )
    result = inventory.transformed()
    assert not inventory.native
    assert result.startswith(html.split('<script src="/custom.js')[0])
    scripts = BeautifulSoup(result, "html.parser").select("[data-admin-htmx-script]")
    assert len(scripts) == 2
    custom, catalog = scripts
    assert custom["data-admin-htmx-src"] == "/custom.js?a=1&b=2"
    assert custom["data-admin-htmx-type"] == "module"
    assert custom["data-admin-htmx-load"] == mode
    assert custom["type"] == "application/json" and custom["nonce"] == "a&b"
    assert custom.has_attr("crossorigin")
    assert not any(custom.has_attr(attr) for attr in ("src", "async", "defer"))
    assert custom.string == 'window.example = "kept";'
    assert catalog["data-admin-htmx-src"] == "/admin/jsi18n/"
