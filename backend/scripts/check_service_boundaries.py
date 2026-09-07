"""Run the real multi-service integration suite using the platform environment."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    raise SystemExit(
        subprocess.call(
            [
                str(root / "platform_service/.venv/bin/python"),
                "-m",
                "pytest",
                str(root / "integration_tests"),
                "-q",
                "-ra",
                *sys.argv[1:],
            ]
        )
    )
