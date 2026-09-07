"""Application assembly. Apply Alembic migrations before serving traffic."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat_colleges, chat_columns, chats, college_directory
from app.configuration.settings import settings
from app.modules.research.internal_router import router as research_internal_router
from app.modules.research.router import router as research_router

app = FastAPI(title="CampusPath Platform Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)
for router in [
    chats.router,
    chat_colleges.router,
    chat_columns.router,
    college_directory.router,
    research_router,
    research_internal_router,
]:
    app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
