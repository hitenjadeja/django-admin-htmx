# Implementation plan

The plan tool is unavailable in this task's callable tool inventory. This durable plan is the implementation tracker; the goal tool tracks the complete deliverable.

1. [complete] Inventory Django admin and upstream behavior; define compatibility and feature/test matrix.
2. [complete] Implement installable app: conservative HTMX transport, lifecycle management, responsive styles, system checks, extension hooks.
3. [complete] Build example covering admin capabilities and meaningful Python/integration tests.
4. [in progress] Exercise actual desktop/mobile UI, implement repeatable browser regression tests, fix lifecycle and UX failures.
5. [pending] Run supported Django version matrix, build wheel/sdist, install wheel into fresh Django projects and verify no source imports.
6. [pending] Complete installation/extension/test/limitations documentation and ordered screenshot evidence; report exact results.

## Constraints

All task files, environments, downloads and evidence remain within this project. Preserve unrelated parent-workspace changes. No publication or Git changes required. Django's authorization, CSRF, validation, ModelAdmin and AdminSite behavior remain authoritative. No sensitive admin HTML is stored in HTMX's localStorage history cache. Opt out to native navigation for incompatible custom integrations.

## Task commits

Each numbered phase is a coherent local commit after its relevant checks pass. The empty project now has its own repository on `codex/htmx-admin`, isolating commits from the parent workspace. No remote publication is requested.

## Required transport version

Use vendored **HTMX 4.0.0**, stable release, explicitly requested by the user. The official site announces 4.0 released, but npm's `latest` intentionally remains on 2.x. Follow https://four.htmx.org/ documentation. Version 4 uses explicit inheritance, colon-separated lifecycle events, fetch-based requests, and server-requested history restoration. Do not use 2.x lifecycle assumptions.
