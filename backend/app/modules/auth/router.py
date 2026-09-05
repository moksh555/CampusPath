"""Google-only OIDC sign-in and application session endpoints."""

import secrets
from datetime import timedelta
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select

from app.configuration.settings import settings
from app.core.database import get_db
from app.core.security import check_origin, get_current_user_id
from app.modules.auth.models import LoginSession, OAuthAttempt, User
from app.modules.auth.repository import upsert_google_user
from app.modules.auth.service import access_token, digest, issue_refresh, now, rotate

router = APIRouter(prefix="/auth", tags=["authentication"])
keys = jwt.PyJWKClient("https://www.googleapis.com/oauth2/v3/certs")


def cookies(response, session, refresh):
    opts = dict(httponly=True, secure=settings.cookie_secure, samesite="lax")
    response.set_cookie(
        "access_token",
        access_token(session),
        max_age=settings.access_minutes * 60,
        path="/",
        **opts,
    )
    response.set_cookie(
        "refresh_token",
        refresh,
        max_age=settings.refresh_days * 86400,
        path="/auth",
        **opts,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/login")
def login(db=Depends(get_db)):
    if (
        not settings.google_client_id
        or not settings.google_client_secret.get_secret_value()
    ):
        raise HTTPException(503, "Configure Google OAuth credentials in backend/.env")
    try:
        settings.signing_key()
    except ValueError as exc:
        raise HTTPException(503, "Configure JWT_SIGNING_KEY in backend/.env") from exc
    state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    db.add(
        OAuthAttempt(
            digest=digest(state), nonce=nonce, expires_at=now() + timedelta(minutes=10)
        )
    )
    db.commit()
    query = urlencode(
        dict(
            client_id=settings.google_client_id,
            redirect_uri=settings.google_redirect_uri,
            response_type="code",
            scope="openid email profile",
            state=state,
            nonce=nonce,
        )
    )
    response = RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + query)
    response.set_cookie(
        "oauth_state",
        state,
        max_age=600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/auth",
    )
    return response


@router.get("/callback")
def callback(request: Request, state: str = "", code: str = "", db=Depends(get_db)):
    if (
        not state
        or not secrets.compare_digest(state, request.cookies.get("oauth_state", ""))
        or not code
    ):
        raise HTTPException(400, "Invalid OAuth callback")
    attempt = db.scalar(
        select(OAuthAttempt)
        .where(OAuthAttempt.digest == digest(state))
        .with_for_update()
    )
    if not attempt or attempt.expires_at <= now():
        raise HTTPException(400, "Sign-in attempt expired")
    nonce = attempt.nonce
    db.delete(attempt)
    db.commit()
    try:
        response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data=dict(
                code=code,
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret.get_secret_value(),
                redirect_uri=settings.google_redirect_uri,
                grant_type="authorization_code",
            ),
            timeout=15,
        )
        response.raise_for_status()
        raw = response.json()["id_token"]
        claims = jwt.decode(
            raw,
            keys.get_signing_key_from_jwt(raw).key,
            algorithms=["RS256"],
            audience=settings.google_client_id,
            issuer=["https://accounts.google.com", "accounts.google.com"],
            options={"require": ["exp", "iat", "sub", "iss", "aud", "nonce"]},
        )
        if (
            not secrets.compare_digest(claims["nonce"], nonce)
            or claims.get("email_verified") is not True
        ):
            raise ValueError("Invalid identity")
    except (httpx.HTTPError, jwt.PyJWTError, ValueError, KeyError) as exc:
        raise HTTPException(400, "Google sign-in could not be verified") from exc
    user = upsert_google_user(db, claims)
    session = LoginSession(
        user_id=user.id, expires_at=now() + timedelta(days=settings.refresh_days)
    )
    db.add(session)
    db.flush()
    refresh = issue_refresh(db, session)
    db.commit()
    result = cookies(RedirectResponse(settings.frontend_origin), session, refresh)
    result.delete_cookie("oauth_state", path="/auth")
    return result


@router.post("/refresh")
def refresh(request: Request, db=Depends(get_db)):
    check_origin(request)
    session, token = rotate(db, request.cookies.get("refresh_token", ""))
    return cookies(JSONResponse({"ok": True}), session, token)


@router.get("/me")
def me(user_id=Depends(get_current_user_id), db=Depends(get_db)):
    user = db.get(User, user_id)
    return {"id": user.id, "name": user.name, "email": user.email}


@router.post("/logout")
def logout(request: Request, db=Depends(get_db)):
    check_origin(request)
    from app.modules.auth.models import RefreshToken

    token = db.get(RefreshToken, digest(request.cookies.get("refresh_token", "")))
    if token:
        session = db.get(LoginSession, token.session_id)
        session.revoked = True
        db.commit()
    response = JSONResponse({"ok": True})
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/auth")
    return response
