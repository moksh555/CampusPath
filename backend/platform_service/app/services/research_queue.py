"""Session jobs with snapshot validation, partial-result retries, and one JSON write."""

from datetime import timedelta

from sqlalchemy import and_, or_, select

from app.core.clock import now
from app.models import Chat
from app.modules.research.contracts import ClaimedJob, SessionPayload
from app.modules.research.models import ResearchJob
from app.services.session_results import ERROR_MESSAGES, document, empty_cell


def enqueue(db, chat):
    # Every dashboard mutation and queue operation locks the chat before its job.
    db.refresh(chat, with_for_update=True)
    job = db.scalar(
        select(ResearchJob).where(ResearchJob.chat_id == chat.id).with_for_update()
    )
    if (
        job
        and job.revision == chat.research_revision
        and job.status in ("queued", "running")
    ):
        return {"queued": 0, "cells": 0}
    result = document(chat)
    targets = []
    for row in chat.colleges:
        cells = result.setdefault(str(row.id), {})
        for column in chat.columns:
            cell = cells.setdefault(str(column.id), empty_cell(row.id, column.id))
            if cell["status"] == "completed":
                continue
            targets.append(dict(row_id=str(row.id), column_id=str(column.id)))
            cell.update(status="queued", error_code=None, error_message=None)
    if not targets:
        return {"queued": 0, "cells": 0}
    chat.research_revision = (chat.research_revision or 0) + 1
    chat.research_results = result
    payload = SessionPayload(
        session_id=chat.id,
        revision=chat.research_revision,
        major=chat.major,
        universities=[
            dict(
                id=row.id, name=row.name, country=row.country, major=row.major_override
            )
            for row in chat.colleges
        ],
        questions=[dict(id=column.id, label=column.label) for column in chat.columns],
        targets=targets,
    )
    if job is None:
        job = ResearchJob(chat_id=chat.id)
        db.add(job)
    job.revision = chat.research_revision
    job.payload = payload.model_dump(mode="json")
    job.attempts = 0
    job.status = "queued"
    job.error_code = job.lease_until = None
    db.commit()
    return {"queued": 1, "cells": len(targets)}


def _locked(db, job_id, *, skip_locked=False):
    candidate = db.scalar(select(ResearchJob).where(ResearchJob.id == job_id))
    if candidate is None:
        return None, None
    chat = db.scalar(
        select(Chat)
        .where(Chat.id == candidate.chat_id)
        .with_for_update(skip_locked=skip_locked)
        .execution_options(populate_existing=True)
    )
    if chat is None:
        return None, None
    job = db.scalar(
        select(ResearchJob)
        .where(ResearchJob.id == job_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return chat, job


def _set_targets(chat, payload, status, code=None):
    result = document(chat)
    for target in payload["targets"]:
        row_id, column_id = target["row_id"], target["column_id"]
        cell = result.setdefault(row_id, {}).setdefault(
            column_id, empty_cell(row_id, column_id)
        )
        cell.update(
            status=status, error_code=code, error_message=ERROR_MESSAGES.get(code)
        )
    chat.research_results = result


def claim(db, timeout_seconds):
    candidates = db.scalars(
        select(ResearchJob.id)
        .where(
            or_(
                ResearchJob.status == "queued",
                and_(ResearchJob.status == "running", ResearchJob.lease_until < now()),
            )
        )
        .limit(32)
    ).all()
    for job_id in candidates:
        chat, job = _locked(db, job_id, skip_locked=True)
        if job is None:
            continue
        if job.revision != chat.research_revision:
            job.status = "superseded"
            db.commit()
            continue
        if job.status not in ("queued", "running") or (
            job.status == "running" and job.lease_until > now()
        ):
            db.rollback()
            continue
        if job.attempts >= 3:
            job.status = "failed"
            job.error_code = "timeout"
            _set_targets(chat, job.payload, "failed", "timeout")
            db.commit()
            continue
        job.attempts += 1
        job.status = "running"
        job.lease_until = now() + timedelta(seconds=timeout_seconds + 30)
        _set_targets(chat, job.payload, "running")
        response = ClaimedJob(
            id=job.id, attempt=job.attempts, revision=job.revision, payload=job.payload
        )
        db.commit()
        return response
    return None


def complete(db, job_id, completion):
    chat, job = _locked(db, job_id)
    if (
        job is None
        or job.attempts != completion.attempt
        or job.revision != completion.revision
        or job.status != "running"
    ):
        return False
    if chat.research_revision != job.revision:
        job.status = "superseded"
        db.commit()
        return False
    payload = SessionPayload.model_validate(job.payload)
    failed = []
    result = document(chat)
    if completion.result is not None:
        completion.result.validate_for(payload)
        for answer in completion.result.cells:
            row_id, column_id = str(answer.row_id), str(answer.column_id)
            cell = result[row_id][column_id]
            if answer.status == "completed":
                cell.update(
                    status="completed",
                    value=answer.answer,
                    sources=[
                        source.model_dump(mode="json") for source in answer.sources
                    ],
                    researched_at=now().isoformat(),
                    error_code=None,
                    error_message=None,
                )
            else:
                failed.append(dict(row_id=row_id, column_id=column_id))
                cell.update(
                    status="queued" if job.attempts < 3 else "failed",
                    error_code=answer.error_code,
                    error_message=ERROR_MESSAGES[answer.error_code],
                )
    else:
        failed = job.payload["targets"]
        code = completion.error_code or "agent_error"
        for target in failed:
            result[target["row_id"]][target["column_id"]].update(
                status="queued" if job.attempts < 3 else "failed",
                error_code=code,
                error_message=ERROR_MESSAGES[code],
            )
    chat.research_results = result
    job.status = ("queued" if job.attempts < 3 else "failed") if failed else "completed"
    job.error_code = completion.error_code or next(
        (result[t["row_id"]][t["column_id"]]["error_code"] for t in failed), None
    )
    job.lease_until = None
    if failed:
        job.payload = {**job.payload, "targets": failed}
    db.commit()
    return True
