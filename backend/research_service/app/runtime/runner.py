"""Child-process entry point for user-owned, import-safe Python agent callables."""

import asyncio
import contextlib
import importlib
import inspect
import json
import sys

from app.contracts import SessionPayload, SessionResult


def invoke(entrypoint: str, payload: dict):
    module, separator, attribute = entrypoint.partition(":")
    if not separator or not module or not attribute or ":" in attribute:
        raise ValueError("AGENT_ENTRYPOINT must be module:function")
    function = getattr(importlib.import_module(module), attribute)
    if not callable(function):
        raise TypeError("Agent entry point must be callable")
    result = function(payload)
    if inspect.isawaitable(result):
        result = asyncio.run(result)
    return SessionResult.model_validate(result).validate_for(
        SessionPayload.model_validate(payload)
    )


def main():
    request = json.load(sys.stdin)
    if request["python_path"]:
        sys.path.insert(0, request["python_path"])
    # Agent/tool prints must not corrupt the JSON response protocol.
    with contextlib.redirect_stdout(sys.stderr):
        result = invoke(request["entrypoint"], request["payload"])
    sys.stdout.write(result.model_dump_json())


if __name__ == "__main__":
    main()
