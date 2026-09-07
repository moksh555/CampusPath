"""Session coordinator: dispatch subagents concurrently and preserve every cell ID."""

import asyncio

from app.contracts import AgentResult, CellResearchResult, SessionPayload, SessionResult
from app.runtime.errors import error_code
from app.settings import settings


async def research(payload: dict) -> dict:
    from app.tools.sub_agents_tool import unit_level_research

    session = SessionPayload.model_validate(payload)
    rows = {row.id: row for row in session.universities}
    columns = {column.id: column for column in session.questions}
    semaphore = asyncio.Semaphore(settings.max_parallel_units)

    async def run(target):
        row = rows[target.row_id]
        async with semaphore:
            try:
                result = await asyncio.wait_for(
                    unit_level_research.ainvoke(
                        {
                            "university": row.name,
                            "country": row.country,
                            "major": row.major or session.major,
                            "question": columns[target.column_id].label,
                        }
                    ),
                    timeout=settings.unit_timeout_seconds,
                )
                answer = AgentResult.model_validate(result)
                return CellResearchResult(
                    **target.model_dump(), status="completed", **answer.model_dump()
                )
            except Exception as error:
                return CellResearchResult(
                    **target.model_dump(), status="failed", error_code=error_code(error)
                )

    # Scheduling is explicit: no LLM can silently omit or invent a row/column pair.
    cells = await asyncio.gather(*(run(target) for target in session.targets))
    return SessionResult(cells=cells).validate_for(session).model_dump(mode="json")
