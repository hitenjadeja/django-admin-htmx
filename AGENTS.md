# Repository instructions

## Project contract

- Enhance Django's own admin with HTMX while preserving its default appearance,
  permissions, CSRF protection, forms, messages and audit behavior.
- Do not introduce a theme, replacement model registry, CDN or JavaScript build
  requirement. Preserve native navigation fallback and the opt-out contract.
- Source lives in `src/admin_htmx/`; `example/` is a local-only demonstration.
  Read `docs/ARCHITECTURE.md` before changing transport or widget lifecycles.
- Preserve the BSD-3-Clause license and the vendored HTMX license.
- Do not commit credentials, real user data, databases, environments or caches.

## Development and validation

Use Python 3.12 or later. Create `.venvs/dev` and install `-e '.[test,dev]'`.
Set `PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright"`, then install Chromium
with `python -m playwright install chromium` (CI also needs `--with-deps`).

- Backend changes: `python -m pytest -m 'not browser' -q`.
- UI, middleware or lifecycle changes: `python -m pytest tests -q`.
- Packaging: `python -m build --outdir dist`,
  `python -m twine check --strict dist/*`, and
  `python scripts/check_release.py --dist-dir dist`.
- Fresh installation: `python scripts/verify_fresh_install.py --skip-build`.
- Version source: `src/admin_htmx/__init__.py`. Add changes to `CHANGELOG.md`.
- Follow `docs/RELEASING.md`; never publish to a package index merely to test CI.
- Keep evidence honest: do not relabel historical test results as a new run.

## Host-only GitHub authentication and publishing

- Never run `gh auth login -h github.com` inside an agent sandbox. Interactive
  GitHub authentication must be completed by the user in a host-machine terminal.
- Ask the user to run `gh auth login -h github.com` and `gh auth status` on the
  host, wait for confirmation, then use host/full-access escalation for
  non-interactive verification and publish commands. Existing session
  confirmation that host authentication is ready is sufficient.
- Do not retry interactive GitHub login in the sandbox or interpret a
  sandbox-only auth failure as the host authentication state.
- Run Git mutations and remote operations on the host with full access. Preserve
  unrelated changes, stage explicit files, keep hooks enabled and never force
  push shared branches or move published version tags.

## Screenshot flow delivery

- After implementing or changing a UI or UX flow, always show an ordered
  screenshot walkthrough of the full affected flow in the final response,
  without waiting to be asked. Include the entry point, key screens, meaningful
  branches, and finish or saved states, with mobile and desktop views where relevant.
- Use actual screenshots of the implemented UI, with readable labels and access
  to the full-size views. A single screenshot or prose-only summary is not enough.
- Use portable relative links in repository documentation. Use absolute local
  screenshot paths when presenting images in the desktop conversation.
