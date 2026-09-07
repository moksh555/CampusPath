"""Sanitized failures that can cross the service boundary without credentials."""

import asyncio

from pydantic import ValidationError


class ResearchFailure(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def error_code(error: Exception) -> str:
    if isinstance(error, ResearchFailure):
        return error.code
    if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
        return "timeout"
    if isinstance(error, ValidationError):
        return "invalid_response"
    # Inspect only to classify; never forward provider messages or credentials.
    message = str(error).lower()
    if "no content" in message or "empty content" in message:
        return "no_content"
    return "provider_error"
