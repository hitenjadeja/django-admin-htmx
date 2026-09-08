#!/usr/bin/env python3
"""Run the same backend/browser suite in each prepared local environment."""

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
results = []
environments = [
    ("django52", "django52"),
    ("django60", "django60"),
    ("django61", "django61"),
]
if (ROOT / ".venvs/python312-django61/bin/python").exists():
    environments.append(("python312-django61", "python312-django61"))
for label, environment in environments:
    python = ROOT / ".venvs" / environment / "bin/python"
    env = {
        **os.environ,
        "PLAYWRIGHT_BROWSERS_PATH": str(ROOT / ".cache/ms-playwright"),
        "TMPDIR": str(ROOT / ".cache/tmp"),
    }
    env["ADMIN_HTMX_SCREENSHOTS"] = "1" if label == "django61" else "0"
    version = subprocess.check_output(
        [python, "-m", "django", "--version"], text=True
    ).strip()
    command = [
        str(python),
        "-m",
        "pytest",
        "tests",
        "-q",
        f"--junitxml=evidence/{label}.xml",
        f"--basetemp=.cache/pytest-{label}",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(result.stdout, flush=True)
    (ROOT / f"evidence/{label}-tests.txt").write_text(result.stdout)
    results.append(
        {
            "environment": label,
            "django": version,
            "python": subprocess.check_output([python, "--version"], text=True).strip(),
            "exit_code": result.returncode,
            "summary": result.stdout.strip().splitlines()[-1],
        }
    )
    (ROOT / "evidence/test-matrix.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )
    if result.returncode:
        raise SystemExit(result.returncode)
