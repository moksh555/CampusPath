"""Versioned HTTP protocol for claiming research and delivering its result."""

from app.contracts import ClaimedJob, SessionResult


class PlatformClient:
    def __init__(self, http):
        self.http = http

    def claim(self, timeout_seconds: int) -> ClaimedJob | None:
        response = self.http.post(
            "/internal/research/v2/claim", json={"timeout_seconds": timeout_seconds}
        )
        response.raise_for_status()
        return (
            None
            if response.status_code == 204
            else ClaimedJob.model_validate(response.json())
        )

    def complete(
        self,
        job: ClaimedJob,
        result: SessionResult | None,
        error_code: str | None = None,
    ):
        response = self.http.post(
            f"/internal/research/v2/jobs/{job.id}/complete",
            json={
                "attempt": job.attempt,
                "revision": job.revision,
                "error_code": error_code,
                "result": result.model_dump(mode="json")
                if result is not None
                else None,
            },
        )
        if response.status_code != 409:
            response.raise_for_status()
