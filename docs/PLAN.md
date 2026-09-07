# Implementation plan

The plan tool is unavailable in this task's callable tool inventory. This durable plan is the implementation tracker; the goal tool tracks the complete deliverable.

1. [complete] Inventory Django admin and upstream behavior; define compatibility and feature/test matrix.
2. [complete] Implement installable app: conservative HTMX transport, lifecycle management, responsive styles, system checks, extension hooks.
3. [complete] Build example covering admin capabilities and meaningful Python/integration tests.
4. [complete] Exercise actual desktop/mobile UI, implement repeatable browser regression tests, fix lifecycle and UX failures.
5. [complete] Run supported Django version matrix, build wheel/sdist, install wheel into fresh Django projects and verify no source imports.
6. [complete] Complete installation/extension/test/limitations documentation and ordered screenshot evidence; report exact results.

## Constraints

All task files, environments, downloads and evidence remain within this project. Preserve unrelated parent-workspace changes. No publication or Git changes required. Django's authorization, CSRF, validation, ModelAdmin and AdminSite behavior remain authoritative. No sensitive admin HTML is stored in HTMX's localStorage history cache. Opt out to native navigation for incompatible custom integrations.

## Task commits

Each numbered phase is a coherent local commit after its relevant checks pass. The empty project now has its own repository on `codex/htmx-admin`, isolating commits from the parent workspace. No remote publication is requested.

## Required transport version

Use vendored **HTMX 4.0.0**, stable release, explicitly requested by the user. The official site announces 4.0 released, but npm's `latest` intentionally remains on 2.x. Follow https://four.htmx.org/ documentation. Version 4 uses explicit inheritance, colon-separated lifecycle events, fetch-based requests, and server-requested history restoration. Do not use 2.x lifecycle assumptions.

## Completed task checkpoints

- `6b8b192` — inventory and concrete implementation/verification plan.
- `9e188ce` — installable HTMX 4 app, transport, lifecycle and responsive styles.
- `02dd244` — complete example and initial 46 backend integration tests.
- `2801c8b` — browser/security/compatibility task, expanded to 49 backend tests and 15 browser scenarios; mobile and lifecycle fixes.

Final matrix: 64 passed on Django 5.2.17, 6.0.8 and 6.1.1 with Python 3.13.0, and 64 passed on Django 6.1.1 with Python 3.12.7. The exact final wheel was installed non-editably and verified in all three independent fresh projects. Each passed migrations, system checks, collectstatic and a real-browser save. The evidence walkthrough contains 52 ordered desktop/mobile screenshots.

- `63ef433` — build scripts, final version matrix and independent fresh-wheel projects with verified import paths.
- Final documentation/evidence task — installation guide, compatibility boundaries, 52-step screenshot gallery and artifact checksums; committed after final archive verification.

All planned implementation tasks are complete. No remote push, publication or deployment was requested or performed.
