"""Authentication and authorization service assembly."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.authentication.router import router as auth_router
from app.authorization.router import router as authorization_router
from app.configuration.settings import settings

app = FastAPI(title="CampusPath Auth Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(auth_router)
app.include_router(authorization_router)


@app.get("/health")
def health():
    return {"status": "ok"}
