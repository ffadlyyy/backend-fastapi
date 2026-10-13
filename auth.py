import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas

from config import TOKEN_MENIT
from database import get_db
from limiter import limiter
from security import HASH_DUMMY, buat_token, hash_password, verify_password

log = logging.getLogger("uvicorn.error")
router = APIRouter(prefix="/auth", tags=["Auth"])


def cek_kredensial(
    db: Session, username: str, password: str
) -> models.User:
    stmt = select(models.User).where(models.User.username == username)
    user = db.scalars(stmt).first()
    hash_tersimpan = user.password_hash if user else ""
    # selalu jalankan bcrypt supaya waktu respons tidak membocorkan
    # apakah username ada atau tidak
    benar = verify_password(password, hash_tersimpan or HASH_DUMMY)
    if user is None or not hash_tersimpan or not benar:
        log.warning("Login gagal username=%r", username)
        raise HTTPException(
            status_code=401,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post(
    "/register", response_model=schemas.UserRead,
    status_code=201,
)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    user = models.User(
        name=data.name,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Username sudah dipakai"
        )
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenOut)
@limiter.limit("10/minute")
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = cek_kredensial(db, form.username, form.password)
    return schemas.TokenOut(access_token=buat_token(user.id))

@router.post("/login-cookie")
@limiter.limit("10/minute")
def login_cookie(
    request: Request,
    response: Response,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    user = cek_kredensial(db, form.username, form.password)
    csrf = secrets.token_hex(16)
    umur = TOKEN_MENIT * 60
    response.set_cookie(
        "access_token",
        buat_token(user.id),
        httponly=True,
        samesite="lax",
        max_age=umur,
    )
    response.set_cookie(
        "csrf_token", csrf, httponly=False, samesite="lax", max_age=umur
    )
    return {"csrf_token": csrf}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("csrf_token")
    return {"pesan": "Anda sudah keluar"}