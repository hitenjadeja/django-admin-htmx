# Changelog

User-visible changes are recorded here. Versions follow Semantic Versioning and
PEP 440, with Git tags named `vX.Y.Z`. During 0.x, minor releases may break the
integration contract; patch releases preserve it. PyPI publication is separate
from a GitHub release.

## [Unreleased]

### Added

- A 95% minimum Python coverage gate, including branches, for unit and Django
  integration tests in pre-commit and every backend CI matrix job. Focused tests
  cover middleware response boundaries, script handling and configuration checks.
- A slim progress bar and visible “Loading…” status after 200 ms for slow admin
  navigation and submissions, lasting through redirects and widget setup.
  Feedback follows Django's light/dark colors and reduced-motion preferences;
  duplicate-submit protection and retained-form error recovery remain active.
- A request-flow diagram, implementation map and error-handling/recovery guide
  in the architecture documentation, linked from the README.
- Pre-commit hooks for Ruff linting/formatting and ty type checking, matching CI
  checks, development dependencies and contributor setup instructions.

### Changed

- Formatted maintained Python code and clarified types for the new checks.

## [0.1.2] - 2026-09-08

### Added

- GitHub CI for Python 3.12–3.14 and Django 5.2, 6.0 and 6.1, Chromium regression
  checks, distribution validation and fresh-project wheel installation checks.
- A manually triggered TestPyPI/PyPI workflow using Trusted Publishing, with
  tag/version/changelog validation and all CI checks before upload.
- Contributor and security guidance, issue and pull request templates,
  dependency update configuration, AGENTS.md and a CLAUDE.md reference.
- Instructions for testing releases in existing projects and later registering
  the project on Django Packages.

### Changed

- Package metadata now includes repository, documentation, issue and changelog
  URLs, explicit license files and supported-version classifiers.
- The package version is declared only in `src/admin_htmx/__init__.py`.
- Screenshot documentation uses portable links for GitHub readers.
- Appearance comparisons wait for native transitions to finish and account for
  Linux control-edge antialiasing while retaining exact style/layout checks.

## [0.1.1] - 2026-09-08

### Fixed

- Restored Django's default styling, stylesheet order and responsive behavior.
- Removed the initial custom theme and extra mobile, save and feedback controls.
- Added native-versus-enhanced appearance checks and fresh wheel verification.

## [0.1.0] - 2026-09-07

### Added

- Initial local distribution: HTMX 4 navigation for Django admin, managed widget
  lifecycles, system checks, opt-outs and custom AdminSite support.
- Example application, backend/browser coverage and an ordered walkthrough.

0.1.0 and 0.1.1 were local builds, not PyPI releases.

[Unreleased]: https://github.com/hitenjadeja/django-admin-htmx/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/hitenjadeja/django-admin-htmx/releases/tag/v0.1.2
[0.1.1]: https://github.com/hitenjadeja/django-admin-htmx/commit/e54282f
[0.1.0]: https://github.com/hitenjadeja/django-admin-htmx/commit/74c29bb
