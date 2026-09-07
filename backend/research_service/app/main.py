"""Research service process lifecycle."""

import logging
import time

import httpx
from pydantic import ValidationError

from app.clients.platform import PlatformClient
from app.settings import settings
from app.worker import run_once


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    token = settings.research_service_token.get_secret_value()
    if len(token) < 32:
        raise ValueError(
            "Set RESEARCH_SERVICE_TOKEN to the same 32+ character secret as platform_service"
        )
    with httpx.Client(
        base_url=settings.platform_service_url,
        timeout=20,
        headers={"Authorization": "Bearer " + token},
    ) as http:
        platform = PlatformClient(http)
        logger.info("Research service started")
        while True:
            try:
                if run_once(platform):
                    continue
            except (httpx.HTTPError, ValidationError, ValueError):
                logger.warning("Platform research API unavailable or invalid; retrying")
            time.sleep(settings.poll_seconds)


if __name__ == "__main__":
    main()
