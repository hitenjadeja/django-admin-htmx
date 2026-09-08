# Contributing

Bug reports and focused pull requests are welcome. Include a minimal reproducer,
Python/Django/package versions, browser details and whether disabling
`ADMIN_HTMX_ENABLED` changes the behavior. Report vulnerabilities privately as
described in [SECURITY.md](SECURITY.md).

## Local development

```sh
git clone https://github.com/hitenjadeja/django-admin-htmx.git
cd django-admin-htmx
python -m venv .venvs/dev
source .venvs/dev/bin/activate
python -m pip install -e '.[test,dev]'
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright"
python -m playwright install chromium
python -m pytest tests -q
```

On Linux, `python -m playwright install --with-deps chromium` installs required
system libraries. Backend-only checks use `python -m pytest -m 'not browser' -q`.
See the README for running and seeding the local demonstration application.

Keep changes focused and preserve Django's behavior and appearance. Add meaningful
regression coverage for behavior changes and an entry under `Unreleased` in the
changelog. UI changes need desktop/mobile screenshots showing entry, validation
or alternate paths and the saved result. See [AGENTS.md](AGENTS.md).

CI runs the supported Python/Django combinations, browser tests, package checks
and installation of the wheel in separate projects. The wheel must contain all
templates, scripts and licenses, and must not include the example or test apps.

Contributions are provided under the project's [BSD-3-Clause license](LICENSE).
Preserve attribution for third-party code. Be respectful and constructive in
issues and reviews.

Maintainers: follow [the release guide](docs/RELEASING.md) for versioning,
GitHub releases, PyPI publication and Django Packages listing.
