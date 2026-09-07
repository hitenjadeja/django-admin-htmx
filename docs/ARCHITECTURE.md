# Architecture and extension contract

Django remains the application. This package does not subclass, replace, or monkeypatch ModelAdmin or AdminSite. The template override extends Django's own `admin/base.html` and adds only styles, metadata and local scripts. The middleware only adapts requests resolved into an admin namespace whose rendered document contains that metadata. It does not trust HTMX headers as proof of authentication or authorization.

## Request lifecycle

1. Ordinary admin links and forms are rendered by Django. After successful initialization, eligible controls receive explicit HTMX 4 attributes. Same-origin URLs within the current AdminSite are enhanced. Modifier clicks, external links, widget anchors, popups, downloads and explicit opt-outs keep their native meanings.
2. HTMX collects real form controls and the clicked submit button; multipart forms retain file uploads and hidden CSRF tokens. One request at a time is admitted through `hx-sync="body:drop"`. A live status region and progress bar communicate request/loading state.
3. Django handles the request normally. Permission, validation, save hooks, messages and audit logging remain stock behavior. For this adapter's requests, 301/302/303 admin redirects become HTTP 200 with `HX-Location`; the next request is a GET. External/non-admin redirects use `HX-Redirect`. Cookies and security headers are retained. Other HTMX integrations' requests are not rewritten.
4. Full HTML documents are returned for both ordinary requests and enhanced requests. HTMX 4 selects and swaps the body with `outerSync`, including its class and data attributes. Page styles and metadata are refreshed before the swap; Django's head media participate in the lifecycle too.
5. Stock script descriptors are inert until the loader runs them in dependency order. Foundational definitions are loaded once. Page scripts (sidebar, theme, filters, cancel, prepopulation and autofocus) run for each new page. Inlines, date/time, filtered selects, autocomplete and action selection are explicitly initialized. Temporary bridges handle jQuery ready/global expectations while a stock script loads; methods/globals are restored immediately afterward.
6. Before a swap, page-scoped global listeners, popups, Select2 state and jQuery element data are cleaned up. After hydration a public load event fires. Error lists or the main landmark receive focus. Body swaps reset scroll; browser history re-fetches authorized documents using HTMX 4's default server-backed restoration. No admin HTML history cache is placed in localStorage.

Server errors leave the current form in place with a focused error message. The adapter never automatically retries a failed POST. File responses are downloaded from the original response body, avoiding duplicate action execution. Session-expiration redirects display Django's login page.

## Custom integrations

- Keep normal ModelAdmin classes, form classes, inlines, actions, template blocks and AdminSite URL registration.
- A custom template extending `admin/base_site.html` participates automatically if it uses stock scripts. A template replacing Django's base entirely keeps native behavior unless it includes the integration itself.
- Unknown scripts make that page use native Django navigation by default. This is deliberate: arbitrary scripts may depend on `DOMContentLoaded` or leak global event handlers. Following an enhanced GET into such a page completes with a full navigation. Its POSTs remain native.
- To opt custom media into the loader, add `data-admin-htmx-load="once"` or `data-admin-htmx-load="page"` on its script element. `once` should register persistent lifecycle callbacks; `page` must tolerate repeat execution (use an IIFE, not top-level lexical declarations).
- Listen on `document` for `admin-htmx:load` to initialize custom controls and `admin-htmx:before-swap` to destroy them. `admin-htmx:error` and `admin-htmx:download` are available for observability. A script loaded `once` during hydration receives that page's load event after it is registered.
- Add `data-admin-htmx="off"` to a control or wrapper, or `hx-boost="false"`, to keep its links/forms native. Use `ADMIN_HTMX_ENABLED = False` to disable enhancement globally.
- Existing `hx-get` / `hx-post` controls are left to their owner. This adapter should be the only HTMX core loaded on an enhanced admin page; do not add a second global HTMX build.

## Supported boundaries

Stock related-object popups keep Django's opener/dismiss protocol and use ordinary full pages. Autocomplete uses Django's existing AJAX endpoint; its transport is Select2's own AJAX. These are intentional compatibility boundaries, not rewritten protocols. Basic HTML login and CRUD work without JavaScript; JavaScript-specific widgets have Django's usual non-JavaScript limitations. File inputs must be reselected after a validation response, as in native Django.

Custom script opt-ins are a developer contract, not an automatic guarantee. Verify rich text editors, unusual custom admin views, third-party themes, custom CSP policies and other browser engines in the integrating project. The package does not claim universal compatibility with arbitrary template replacements or media. See COVERAGE.md and VERIFICATION.md for measured coverage.
