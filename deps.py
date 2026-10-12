import secrets
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
from database import get_db
from security import baca_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login", auto_error=False
)


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    x_csrf_token: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> models.User:
    dari_cookie = token is None
    if dari_cookie:
        token = request.cookies.get("access_token")
    user_id = baca_token(token) if token else None
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Belum login atau sesi sudah berakhir",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if dari_cookie and request.method not in ("GET", "HEAD", "OPTIONS"):
        cookie_csrf = request.cookies.get("csrf_token", "")
        if not x_csrf_token or not secrets.compare_digest(
            cookie_csrf, x_csrf_token
        ):
            raise HTTPException(
                status_code=403, detail="Token CSRF tidak valid"
            )
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Belum login atau sesi sudah berakhir",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(
    saya: models.User = Depends(get_current_user),
) -> models.User:
    if saya.role != "admin":
        raise HTTPException(status_code=403, detail="Khusus admin")
    return saya