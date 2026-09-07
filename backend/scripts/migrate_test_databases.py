"""Apply each service's migrations only to its explicitly configured test database."""

import os
import subprocess
from pathlib import Path

from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
for name in ("auth_service", "platform_service"):
    directory = root / name
    url = os.environ.get("TEST_DATABASE_URL") or dotenv_values(
        directory / ".env.test"
    ).get("TEST_DATABASE_URL")
    if not url:
        raise SystemExit(
            f"Set TEST_DATABASE_URL in {name}/.env.test before migrating test data"
        )
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    subprocess.run(
        [str(directory / ".venv/bin/python"), "-m", "alembic", "upgrade", "head"],
        cwd=directory,
        env=env,
        check=True,
    )
    print(f"{name}: test database migration passed")
