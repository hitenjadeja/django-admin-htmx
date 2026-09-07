# Capability and verification matrix

Initial inventory (2026-09-07). Each row requires backend verification where applicable and actual browser verification. Final measured coverage is recorded here as tests are completed; planned coverage is not a claim of verification.

| Capability | Required cases | Verification status |
|---|---|---|
| Authentication | login failure/success, next URL, logout POST, session expiration, password error/success | Planned |
| Landing/navigation | dashboard, app index, custom AdminSite, breadcrumbs, sidebar, browser back/forward, direct/deep links | Planned |
| Changelist | search, list filters, facets, sorting, pagination, date hierarchy, empty results | Planned |
| Editing | add/change, field/nonfield errors, save, continue, add another, save as, preserved filters | Planned |
| Deletion/history | cancel/confirm delete, protected delete, history log entries | Planned |
| Actions | selection, select across, custom action, intermediate confirmation, delete selected, download response | Planned |
| List editable | changes saved and invalid values rendered | Planned |
| Inlines | tabular/stacked, add/remove, validation, save, repeated navigation | Planned |
| Relations | FK dropdown, raw ID, add/change/delete popups, autocomplete, M2M filtered selector | Planned |
| Widgets | date/time shortcuts/calendar, prepopulation, file upload/clear, readonly/collapsible fieldsets | Planned |
| Security/compatibility | CSRF rejected/accepted, staff gate, view-only permissions, custom template/media/site, non-admin isolation | Planned |
| Reactive UX | HTMX network requests, busy state, recovery on failures, focus, keyboard, no duplicated handlers | Planned |
| Responsive UX | desktop/mobile dashboard/list/form/confirmations, contained table overflow, accessible navigation and filters | Planned |
| Fallback | no JavaScript CRUD; custom opt-out; popups and downloads remain native where necessary | Planned |
| Distribution | wheel/sdist contents, collectstatic, fresh-project install, supported Django matrix | Planned |

## Primary sources consulted

- https://www.djangoproject.com/download/ — current supported lines: 5.2 LTS (5.2.17), 6.0 (6.0.8), 6.1 (6.1.1), observed 2026-09-07.
- https://docs.djangoproject.com/en/6.1/ref/contrib/admin/ — ModelAdmin options, media, inlines, template overrides, AdminSite extension points.
- https://htmx.org/docs/ — boost, history, request/response headers, status handling, CSRF and script configuration. 3xx response headers are hidden by browser redirect handling, so adapter redirects must use non-3xx HTMX responses.
- https://htmx.org/ and https://four.htmx.org/docs#installation — HTMX 4.0 released; exact vendored version 4.0.0 (stable), not npm's `latest` alias.
- https://four.htmx.org/docs#migrating-from-htmx-2x-to-4x — explicit inheritance, renamed lifecycle events, default swapping of errors, server-fetched history.
