"""Adapt transport only: Django continues to own routing, validation and security."""
import json
from html import escape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse
from django.urls import Resolver404, resolve
from django.utils.cache import patch_vary_headers

# Only stock scripts with a maintained lifecycle adapter may be deferred.
STOCK_SCRIPTS = (
    "theme.js", "nav_sidebar.js", "core.js", "jquery.init.js", "actions.js",
    "inlines.js", "prepopulate.js", "prepopulate_init.js", "change_form.js",
    "urlify.js", "calendar.js", "SelectBox.js", "SelectFilter2.js", "autocomplete.js",
    "filters.js", "cancel.js", "admin/DateTimeShortcuts.js", "admin/RelatedObjectLookups.js",
    "vendor/jquery/jquery.js", "vendor/jquery/jquery.min.js",
    "vendor/xregexp/xregexp.js", "vendor/xregexp/xregexp.min.js",
    "vendor/select2/select2.full.js", "vendor/select2/select2.full.min.js",
)


def is_admin_path(path):
    try:
        return "admin" in resolve(path).app_names
    except Resolver404:
        return False


class ScriptInventory(HTMLParser):
    """Inspect script starts without reserializing the rest of an admin template."""

    def __init__(self, html, known, catalog):
        super().__init__(convert_charrefs=False)
        self.html = html
        self.known = known
        self.catalog = catalog
        self.edits = []
        self.native = False
        self.offsets = [0]
        for line in html.splitlines(keepends=True):
            self.offsets.append(self.offsets[-1] + len(line))
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag != "script":
            return
        values = dict(attrs)
        src = values.get("src", "")
        script_type = values.get("type", "")
        if script_type not in ("", "text/javascript", "application/javascript", "module"):
            return
        if src in self.known["runtime"]:
            return
        path = urlsplit(src).path
        mode = values.get("data-admin-htmx-load")
        known = src in self.known["stock"] or path == self.catalog
        if not known and mode not in ("once", "page"):
            self.native = True
            return
        line, column = self.getpos()
        start = self.offsets[line - 1] + column
        original = self.get_starttag_text()
        safe_attrs = [(key, val) for key, val in attrs if key not in ("src", "type", "defer", "async")]
        safe_attrs.extend([
            ("type", "application/json"), ("data-admin-htmx-script", ""),
            ("data-admin-htmx-src", src), ("data-admin-htmx-type", script_type),
        ])
        serialized = "<script" + "".join(
            f' {key}' if val is None else f' {key}="{escape(val, quote=True)}"'
            for key, val in safe_attrs
        ) + ">"
        self.edits.append((start, start + len(original), serialized))

    def transformed(self):
        html = self.html
        for start, end, replacement in reversed(self.edits):
            html = html[:start] + replacement + html[end:]
        return html


class AdminHtmxMiddleware:
    """Install near the start of MIDDLEWARE (before compression/cache middleware)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(settings, "ADMIN_HTMX_ENABLED", True):
            return response
        if not request.resolver_match or "admin" not in request.resolver_match.app_names:
            return response
        enhanced = request.headers.get("X-Admin-HTMX") == "true" and request.headers.get("HX-Request") == "true"
        patch_vary_headers(response, ("HX-Request", "X-Admin-HTMX"))
        if enhanced and response.status_code in (301, 302, 303):
            location = response["Location"]
            absolute = urlsplit(urljoin(request.build_absolute_uri(), location))
            same_origin = (absolute.scheme, absolute.netloc) == (request.scheme, request.get_host())
            if same_origin and is_admin_path(absolute.path):
                # Keep response cookies and security headers; do not replay the POST.
                response.status_code = 200
                response.content = b""
                del response["Location"]
                response["HX-Location"] = json.dumps({
                    "path": location, "target": "body", "select": "body", "swap": "outerSync",
                    "headers": {"X-Admin-HTMX": "true"},
                })
            else:
                response.status_code = 200
                response.content = b""
                del response["Location"]
                response["HX-Redirect"] = location
            return response
        if response.streaming or response.status_code != 200:
            return response
        if "text/html" not in response.get("Content-Type", "") or response.get("Content-Encoding"):
            return response
        html = response.content.decode(response.charset)
        marker = '<meta name="admin-htmx-root" content="'
        if marker not in html or "_popup" in request.GET or "_popup" in request.POST:
            return response
        root = html.split(marker, 1)[1].split('"', 1)[0]
        runtime = {staticfiles_storage.url("admin_htmx/" + path) for path in ("admin.js", "vendor/htmx-4.0.0.js")}
        stock = {staticfiles_storage.url("admin/js/" + path) for path in STOCK_SCRIPTS}
        # Select2 translations are optional stock media with a locale-specific name.
        from django.contrib.admin.widgets import SELECT2_TRANSLATIONS
        stock.update(staticfiles_storage.url(f"admin/js/vendor/select2/i18n/{lang}.js") for lang in set(SELECT2_TRANSLATIONS.values()))
        inventory = ScriptInventory(html, {"runtime": runtime, "stock": stock}, root + "jsi18n/")
        if inventory.native:
            response["X-Admin-HTMX-Native"] = "true"
            return response
        html = inventory.transformed().replace("</head>", '<meta name="admin-htmx-enhanced" content="true"></head>', 1)
        response.content = html.encode(response.charset)
        response["X-Admin-HTMX-Page"] = "true"
        if "Content-Length" in response:
            response["Content-Length"] = len(response.content)
        return response
