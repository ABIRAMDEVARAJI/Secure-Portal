import logging

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.database import get_db
from app.dependencies import get_current_user, validate_origin
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.auth_service import create_user_session, delete_user_session, upsert_google_user


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def session_cookie(response: RedirectResponse, token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


@router.get("/login")
async def login(request: Request):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth is not configured")
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        profile = token.get("userinfo") or await oauth.google.userinfo(token=token)
        if not profile or not profile.get("email") or not profile.get("sub"):
            raise ValueError("Google identity did not include required claims")
        user = upsert_google_user(db, dict(profile))
        session_token = create_user_session(db, user)
        response = RedirectResponse(settings.FRONTEND_URL, status_code=status.HTTP_302_FOUND)
        session_cookie(response, session_token)
        logger.info("Google login succeeded for user id %s", user.id)
        return response
    except Exception as exc:
        logger.warning("Google login failed: %s", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google authentication failed") from exc


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: Session = Depends(get_db)):
    validate_origin(request)
    delete_user_session(db, request.cookies.get(settings.SESSION_COOKIE_NAME))
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
    return response