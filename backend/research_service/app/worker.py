"""Research orchestration, independent of HTTP and child-process details."""

import logging

from app.runtime.errors import error_code
from app.runtime.executor import AgentExecutor
from app.settings import settings

logger = logging.getLogger(__name__)


def run_once(platform, agent=None):
    job = platform.claim(settings.agent_timeout_seconds)
    if job is None:
        return False
    result = None
    failure = None
    try:
        result = (agent or AgentExecutor()).research(
            job.payload.model_dump(mode="json")
        )
    except Exception as error:
        failure = error_code(error)
        logger.warning("Research attempt failed: %s", failure)
    platform.complete(job, result, failure)
    return True
