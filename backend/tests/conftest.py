"""Load test configuration before application settings are imported."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Explicit shell/CI configuration takes precedence over the local test file.
load_dotenv(Path(__file__).resolve().parents[1] / ".env.test", override=False)
if os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
