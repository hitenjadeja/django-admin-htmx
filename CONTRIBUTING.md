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
python -m pre_commit install
python -m pre_commit run --all-files
export PLAYWRIGHT_BROWSERS_PATH="$PWD/.cache/ms-playwright"
python -m playwright install chromium
python -m pytest tests -q
```

On Linux, `python -m playwright install --with-deps chromium` installs required
system libraries. Unit and Django integration checks with the coverage gate use
`python -m pytest tests -m 'not browser' --cov -q`.
See the README for running and seeding the local demonstration application.

The commit hooks run Ruff lint fixes and formatting, followed by ty type checking
over `src/`, `example/`, `tests/` and `scripts/`, then the complete unit and Django
integration suite with at least 95% Python coverage, including branches.
Generated `fresh_install/` projects are excluded. Ruff may change files; review and stage those changes
before committing again. Run `python -m pre_commit run --all-files` at any time
to run the same checks as CI.

The ty and coverage hooks resolve dependencies from the project's extras in
isolated environments, so they also work without activating `.venvs/dev` and do
not change the development environment. Their uv runners may create a local
`uv.lock`, which is ignored by Git. The first run needs network access to install
the hooks and dependencies. With the development
environment activated, standalone checks are `ruff check .`,
`ruff format --check .` and `ty check`. Keep the Ruff and ty versions in
`pyproject.toml` aligned with their hook revisions when updating them.

The coverage hook runs once per commit, including deletions and documentation-only
changes; it never limits testing to staged filenames. Coverage measures all Python
modules in `src/admin_htmx/`, excluding the example and tests by source scope.
The shared threshold and branch settings live in `pyproject.toml`. Chromium is
not needed for this hook. Browser end-to-end tests and fresh-wheel integration
checks run separately in CI; this percentage does not measure JavaScript or
template coverage. See [the test inventory](docs/COVERAGE.md).

Keep changes focused and preserve Django's behavior and appearance. Add meaningful
regression coverage for behavior changes and an entry under `Unreleased` in the
changelog. UI changes need desktop/mobile screenshots showing entry, validation
or alternate paths and the saved result. See [AGENTS.md](AGENTS.md).

CI runs all pre-commit hooks, the coverage gate on the supported Python/Django
combinations, browser tests, package checks and installation of the wheel in
separate projects. The wheel must contain all
templates, scripts and licenses, and must not include the example or test apps.

Contributions are provided under the project's [BSD-3-Clause license](LICENSE).
Preserve attribution for third-party code. Be respectful and constructive in
issues and reviews.

Maintainers: follow [the release guide](docs/RELEASING.md) for versioning,
GitHub releases, PyPI publication and Django Packages listing.
