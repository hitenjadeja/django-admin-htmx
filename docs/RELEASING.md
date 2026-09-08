# Versioning and releases

Repository: https://github.com/hitenjadeja/django-admin-htmx

There are three separate destinations: GitHub hosts source and downloadable
releases; PyPI distributes the installable package; Django Packages is a
directory listing that references the repository and PyPI project.

## Version policy

`src/admin_htmx/__init__.py` is the only version declaration. Setuptools reads
`__version__` when building. Use Semantic Versioning with PEP 440-compatible
values: `0.1.2`, or `0.2.0rc1` for a release candidate. Tags are `v0.1.2` and
`v0.2.0rc1`. Never move a published tag or reuse a published package version.

During 0.x, a minor release can break the integration contract; patches preserve
it. At 1.x and later, breaking changes require a major release. Every release has
a dated changelog entry. Keep pending changes under `Unreleased`.

## Prepare and publish a GitHub release

1. Update the version, move applicable changes into a dated changelog section,
   and update installation examples and comparison links.
2. Install `.[test,dev]`, run the tests and build into a clean output directory:

   ```sh
   python -m pytest tests -q
   python -m build --outdir dist/release
   python -m twine check --strict dist/release/*
   python scripts/check_release.py --tag v0.1.2 --dist-dir dist/release --notes .cache/release-notes.md
   python scripts/verify_fresh_install.py --skip-build --dist-dir dist/release
   ```

   Create `.cache/` first if needed. Use a new empty output directory for each
   release so stale archives cannot be uploaded. `build` builds the wheel from
   the sdist. Validation checks metadata, package assets, licenses and release
   identity; fresh installation verifies actual admin behavior outside `src/`.
3. Commit and push the changes to `main` on the host, with hooks enabled. Wait
   for **CI success**. All state-changing Git/GitHub commands run on the host.
4. Create and push an annotated tag at the verified commit:

   ```sh
   git tag -a v0.1.2 -m "Release 0.1.2"
   git push origin v0.1.2
   ```

5. Wait for tag CI. Publish a GitHub release with the changelog notes, wheel and
   sdist. Prefer the `distributions` artifact from that successful tag CI run:

   ```sh
   gh run download RUN_ID --name distributions --dir .cache/release-assets
   gh release create v0.1.2 --verify-tag --title "0.1.2" \
     --notes-file .cache/release-notes.md .cache/release-assets/*
   ```

   Replace the version and run ID for each release. Mark release candidates as
   prereleases with `--prerelease`. Test the pinned Git install and release wheel
   in a consuming project. Creating a GitHub release does not publish to PyPI.

## One-time PyPI and TestPyPI account setup

When ready to publish, sign in to your PyPI and TestPyPI accounts and complete
their account/2FA requirements. These are separate accounts and indexes.

Register a pending publisher at [PyPI](https://pypi.org/manage/account/publishing/)
and, for rehearsal, [TestPyPI](https://test.pypi.org/manage/account/publishing/):

| Field | PyPI | TestPyPI |
|---|---|---|
| Project name | `django-admin-htmx` | `django-admin-htmx` |
| Owner | `hitenjadeja` | `hitenjadeja` |
| Repository | `django-admin-htmx` | `django-admin-htmx` |
| Workflow filename | `publish.yml` | `publish.yml` |
| Environment | `pypi` | `testpypi` |

If you already own a project of this name, add its Trusted Publisher through
the project's Publishing page instead. A pending publisher does not reserve a
name; check availability before the first release. No PyPI API token or password
belongs in GitHub secrets for this workflow.

In GitHub Settings → Environments, use environments named `pypi` and `testpypi`,
restrict deployment to `v*` tags and require the maintainer's approval. Keep
self-approval allowed when the same sole maintainer initiates releases.

## Publish a verified tag to a package index

Run **Publish package** explicitly for an existing version tag. Start with
TestPyPI:

```sh
gh workflow run publish.yml --ref v0.1.2 -f repository=testpypi
```

The workflow validates the tag and changelog, reruns the entire CI workflow and
builds distributions. It uploads only the artifacts tested in fresh projects.
Approve the environment deployment when verification succeeds. Only the final
upload job receives OIDC permission; it does not check out or execute project code.

After upload, test in a fresh environment. Install Django from normal PyPI first
and install this package from TestPyPI without dependency resolution:

```sh
python -m pip install 'Django>=5.2,<6.2'
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps django-admin-htmx==0.1.2
python -m pip check
```

Then run the same workflow/tag with `-f repository=pypi` and approve the `pypi`
environment. Verify a fresh `pip install django-admin-htmx==0.1.2` and follow
[the integration checks](INTEGRATION.md). Update the README to prefer the PyPI
command only after that release is available. Duplicate version uploads fail;
the workflow deliberately does not silently skip existing files.

## Django Packages listing

Once the public repository and install instructions are ready, sign in at
[Django Packages](https://djangopackages.org/), search for an existing listing,
and use **Add Package** if one does not exist. Suggested fields:

- Repository URL: `https://github.com/hitenjadeja/django-admin-htmx`
- Name: `django-admin-htmx`
- Category: App (a reusable Django application)
- Description: Django's default admin with HTMX navigation and managed widget lifecycles.
- Documentation: `https://github.com/hitenjadeja/django-admin-htmx#readme`
- PyPI package name: `django-admin-htmx`, once it has actually been published.

Add the project to the relevant admin comparison grid and describe only supported,
tested features. Django Packages is a catalog; there is no wheel-upload pipeline
to configure there. Check that the repository, version, license and PyPI links
display correctly after registration.

## CI costs and maintenance

The workflows use standard `ubuntu-latest` hosted runners, which are free for
public repositories. Larger runners are charged separately. Artifacts and caches
have storage allowances; these workflows retain small distribution archives for
seven days and do not create dependency caches. Dependabot checks Python
dependencies and pinned GitHub Actions weekly. HTMX is vendored, so upstream
HTMX security/release updates need manual review and regression testing.

References, checked 2026-09-08:
[GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions),
[PyPI pending publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
[PyPI publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/),
[Django Packages](https://djangopackages.org/faq/).
