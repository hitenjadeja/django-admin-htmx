#!/usr/bin/env python3
"""Validate release identity and the actual wheel/sdist before publication."""

import argparse
import ast
import re
import tarfile
import zipfile
from email.parser import Parser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "django_admin_htmx"


def read_version(root=ROOT):
    tree = ast.parse((root / "src/admin_htmx/__init__.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        ):
            version = ast.literal_eval(node.value)
            if isinstance(version, str) and re.fullmatch(
                r"\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?", version
            ):
                return version
    raise ValueError("Declare a literal PEP 440 version in src/admin_htmx/__init__.py")


def release_notes(version, root=ROOT):
    changelog = (root / "CHANGELOG.md").read_text()
    match = re.search(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\n(.*?)(?=^## |^\[Unreleased\]:|\Z)",
        changelog,
        re.MULTILINE | re.DOTALL,
    )
    if not match or not match.group(1).strip():
        raise ValueError(f"Missing dated, nonempty changelog entry for {version}")
    return match.group(1).strip() + "\n"


def check_distributions(directory, version):
    wheel = directory / f"{PACKAGE}-{version}-py3-none-any.whl"
    source = directory / f"{PACKAGE}-{version}.tar.gz"
    archives = set(directory.glob("*.whl")) | set(directory.glob("*.tar.gz"))
    if archives != {wheel, source}:
        raise ValueError(
            "Build into a clean directory containing only this version's wheel and sdist"
        )
    required = {
        "admin_htmx/__init__.py",
        "admin_htmx/py.typed",
        "admin_htmx/templates/admin/base.html",
        "admin_htmx/static/admin_htmx/admin.js",
        "admin_htmx/static/admin_htmx/loading.css",
        "admin_htmx/static/admin_htmx/vendor/htmx-4.0.0.js",
        "admin_htmx/static/admin_htmx/vendor/HTMX-LICENSE",
        "admin_htmx/templatetags/admin_htmx.py",
    }
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        missing = required - names
        if missing:
            raise ValueError(f"Wheel missing package assets: {sorted(missing)}")
        if any(
            (
                name.endswith(".css")
                and name != "admin_htmx/static/admin_htmx/loading.css"
            )
            or name.endswith(".sqlite3")
            or name.startswith(("tests/", "example/"))
            for name in names
        ):
            raise ValueError("Wheel contains a theme, database, example or test app")
        metadata_dir = f"{PACKAGE}-{version}.dist-info"
        metadata = Parser().parsestr(archive.read(f"{metadata_dir}/METADATA").decode())
        if metadata["Name"] != "django-admin-htmx" or metadata["Version"] != version:
            raise ValueError("Built package name/version differs from the source")
        if metadata["License-Expression"] != "BSD-3-Clause":
            raise ValueError("Expected BSD-3-Clause license metadata")
        for license_file in (
            "LICENSE",
            "src/admin_htmx/static/admin_htmx/vendor/HTMX-LICENSE",
        ):
            if f"{metadata_dir}/licenses/{license_file}" not in names:
                raise ValueError(f"Missing distribution license: {license_file}")
    with tarfile.open(source) as archive:
        prefix = f"{PACKAGE}-{version}/"
        names = {name.removeprefix(prefix) for name in archive.getnames()}
        required_source = {
            "pyproject.toml",
            "LICENSE",
            "README.md",
            "CHANGELOG.md",
            "AGENTS.md",
            "CLAUDE.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "tests/conftest.py",
            "example/catalog/models.py",
            "scripts/check_release.py",
            "scripts/verify_fresh_install.py",
        }
        missing = required_source - names
        if missing:
            raise ValueError(f"Source distribution missing files: {sorted(missing)}")
        if any(name.endswith(".sqlite3") or "/.env" in name for name in names):
            raise ValueError("Source distribution contains local runtime files")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Require the Git tag to equal v<package version>")
    parser.add_argument("--dist-dir", type=Path)
    parser.add_argument(
        "--notes", type=Path, help="Write this release's changelog notes"
    )
    args = parser.parse_args()
    version = read_version()
    if args.tag and args.tag != f"v{version}":
        parser.error(f"Tag {args.tag!r} does not match package version v{version}")
    notes = release_notes(version)
    if args.dist_dir:
        check_distributions(args.dist_dir, version)
    if args.notes:
        args.notes.write_text(notes)
    print(f"Release {version}: validation passed")


if __name__ == "__main__":
    main()
