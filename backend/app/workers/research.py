"""Run separately: python -m app.workers.research. PostgreSQL leases allow recovery."""

import time
from datetime import timedelta

from sqlalchemy import and_, or_, select

from app.configuration.settings import settings
from app.core.database import SessionLocal
from app.integrations.agent.client import AgentClient
from app.models import Cell
from app.modules.auth.service import now
from app.modules.research.models import ResearchJob


def run_once(client=None) -> bool:
    client = client or AgentClient()
    with SessionLocal() as db:
        job = db.scalar(
            select(ResearchJob)
            .where(
                or_(
                    ResearchJob.status == "queued",
                    and_(
                        ResearchJob.status == "running", ResearchJob.lease_until < now()
                    ),
                )
            )
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return False
        cell = db.get(Cell, job.cell_id)
        if cell is None or cell.revision != job.revision:
            job.status = "superseded"
            db.commit()
            return True
        if job.attempts >= 3:
            job.status = "failed"
            cell.status = "failed"
            db.commit()
            return True
        job.attempts += 1
        attempt = job.attempts
        job.status = cell.status = "running"
        job.lease_until = now() + timedelta(seconds=settings.agent_timeout_seconds + 30)
        job_id, revision, payload = job.id, job.revision, job.payload
        db.commit()
    result = None
    try:
        result = client.research(payload)
    except Exception:
        # Do not persist exceptions: provider messages may contain credentials.
        pass
    with SessionLocal() as db:
        job = db.scalar(
            select(ResearchJob).where(ResearchJob.id == job_id).with_for_update()
        )
        if job is None or job.attempts != attempt:
            return True
        cell = db.scalar(select(Cell).where(Cell.id == job.cell_id).with_for_update())
        if cell is None or cell.revision != revision:
            job.status = "superseded"
        elif result is not None:
            cell.value = result.answer
            cell.sources = [source.model_dump(mode="json") for source in result.sources]
            cell.researched_at = now()
            job.status = cell.status = "completed"
        else:
            job.status = cell.status = "queued" if attempt < 3 else "failed"
        db.commit()
    return True


def main():
    while True:
        if not run_once():
            time.sleep(2)


if __name__ == "__main__":
    main()
