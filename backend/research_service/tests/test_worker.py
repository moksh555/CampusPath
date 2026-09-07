import json
import uuid
from unittest.mock import Mock

import httpx
from app.clients.platform import PlatformClient
from app.contracts import CellResearchResult, SessionResult
from app.runtime.errors import ResearchFailure
from app.worker import run_once


def test_idle_does_not_invoke_agent():
    agent = Mock()
    with httpx.Client(
        base_url="http://platform",
        transport=httpx.MockTransport(lambda r: httpx.Response(204)),
    ) as http:
        assert run_once(PlatformClient(http), agent) is False
    agent.research.assert_not_called()


def test_batch_sent_once_and_revision_forwarded(payload):
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.path.endswith("/claim"):
            return httpx.Response(
                200,
                json=dict(
                    id=str(uuid.uuid4()),
                    attempt=1,
                    revision=1,
                    payload=payload.model_dump(mode="json"),
                ),
            )
        return httpx.Response(204)

    result = SessionResult(
        cells=[
            CellResearchResult(**t.model_dump(), status="completed", answer="Verified")
            for t in payload.targets
        ]
    )
    agent = Mock(research=Mock(return_value=result))
    with httpx.Client(
        base_url="http://platform", transport=httpx.MockTransport(handle)
    ) as http:
        assert run_once(PlatformClient(http), agent)
    assert len(requests) == 2
    assert "/v2/" in requests[0].url.path
    assert json.loads(requests[1].content)["revision"] == 1
    agent.research.assert_called_once_with(payload.model_dump(mode="json"))


def test_process_failure_is_sanitized(payload):
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.path.endswith("/claim"):
            return httpx.Response(
                200,
                json=dict(
                    id=str(uuid.uuid4()),
                    attempt=1,
                    revision=1,
                    payload=payload.model_dump(mode="json"),
                ),
            )
        return httpx.Response(204)

    with httpx.Client(
        base_url="http://platform", transport=httpx.MockTransport(handle)
    ) as http:
        run_once(
            PlatformClient(http),
            Mock(research=Mock(side_effect=ResearchFailure("no_content"))),
        )
    body = json.loads(requests[1].content)
    assert body["error_code"] == "no_content" and body["result"] is None
