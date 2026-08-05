from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate the Bearer access token and return the authenticated User.

    Raises:
        HTTPException 401: If the token is missing, invalid, expired, or the
            user does not exist / is inactive.
    """
    _unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Could not validate credentials.",
                "details": None,
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise _unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
    except (JWTError, Exception):
        raise _unauthorized

    if payload is None:
        raise _unauthorized

    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise _unauthorized

    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        raise _unauthorized

    try:
        user: User | None = db.query(User).filter(User.id == user_id).first()
    except Exception:
        raise _unauthorized

    if user is None:
        raise _unauthorized

    if not user.is_active:
        raise _unauthorized

    return user
