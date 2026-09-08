# Test in an existing Django project

Use the project's normal virtual environment and a development/test database.
The package supports Python 3.12+ and Django >=5.2,<6.2. Keep the project's
existing Django constraint when resolving dependencies.

## Install a known version

```sh
python -m pip install "django-admin-htmx @ git+https://github.com/hitenjadeja/django-admin-htmx.git@v0.1.2"
# With uv instead:
uv add "django-admin-htmx @ git+https://github.com/hitenjadeja/django-admin-htmx.git@v0.1.2"
```

The `pip` command requires Git. The downloadable GitHub release wheel does not.
Add the direct reference to your requirements file, or commit your updated
`pyproject.toml` and lockfile when using uv. The distribution is `django-admin-htmx`;
the Django app and Python import name are `admin_htmx`.

## Enable it

Insert `"admin_htmx"` immediately before `"django.contrib.admin"` in
`INSTALLED_APPS`. Append `"admin_htmx.middleware.AdminHtmxMiddleware"` to
`MIDDLEWARE`. Existing ModelAdmin registrations and admin URLs stay in place.

```sh
python manage.py check
python manage.py collectstatic --noinput
python -m pip check
python -c "import admin_htmx; print(admin_htmx.__version__)"
```

The middleware must come after GZipMiddleware, ConditionalGetMiddleware and
UpdateCacheMiddleware if present. System checks identify ordering problems.
The package does not add migrations or model tables.

## Exercise your application's admin

1. Log in, navigate between model lists and use search, filters and pagination.
2. Add an object, submit an invalid form, correct it and save successfully.
3. Try your inlines, autocomplete, related popups, uploads and custom actions.
4. Check permissions with a restricted staff user, browser back/forward and logout.
5. Repeat key flows at mobile width and with your usual theme/CSP settings.
6. Run your project's normal automated tests.

Django's normal styling should remain intact. Custom scripts without a declared
lifecycle fall back to native navigation. See [the extension contract](ARCHITECTURE.md)
if you need custom widgets to participate in HTMX navigation. Avoid loading a
second HTMX core on the admin page.

## Disable or remove

For an immediate fallback, set `ADMIN_HTMX_ENABLED = False`, restart the Django
process and reload open admin pages. To remove the integration, remove the app
and middleware entries, uninstall the distribution/update the lockfile, then run
your normal deployment and static-file collection process. No library migrations
need reversing.

## Upgrade

Read [CHANGELOG.md](../CHANGELOG.md), change the pinned tag or wheel version,
update the environment/lockfile, collect static assets and reload open admin
pages. Keep the previous pin available for rollback. Once the project is
published to PyPI, a version constraint such as `django-admin-htmx==0.1.2` can
replace the Git reference; check availability before changing it.
